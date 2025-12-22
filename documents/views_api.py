from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from .models import Document, Folder, Cabinet, Group
from .pdf_utils import encrypt_pdf
import json
import os
from datetime import datetime


@method_decorator(csrf_exempt, name='dispatch')
class APILoginView(View):
    """API認証ログイン"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            user = authenticate(request, username=email, password=password)
            
            if user is not None and user.user_type == 'api':
                login(request, user)
                return JsonResponse({
                    'status': 'success',
                    'message': 'ログインに成功しました'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': '認証に失敗しました'
                }, status=401)
        
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class APILogoutView(View):
    """APIログアウト"""
    
    def post(self, request):
        logout(request)
        return JsonResponse({
            'status': 'success',
            'message': 'ログアウトしました'
        })


@method_decorator(csrf_exempt, name='dispatch')
class APIDocumentUploadView(View):
    """請求書PDF登録API"""
    
    @transaction.atomic
    def post(self, request):
        # 認証チェック
        if not request.user.is_authenticated or request.user.user_type != 'api':
            return JsonResponse({
                'status': 'error',
                'message': '認証が必要です'
            }, status=401)
        
        try:
            # パラメータ取得
            client_code = request.POST.get('client_code')
            encrypt_flag = request.POST.get('encrypt_flag', 'false').lower() == 'true'
            pdf_file = request.FILES.get('file')
            
            # バリデーション
            if not client_code or not pdf_file:
                return JsonResponse({
                    'status': 'error',
                    'message': '必須パラメータが不足しています'
                }, status=400)
            
            # ファイル名解析
            file_name = pdf_file.name
            
            # ファイル名から情報を抽出
            # 例: 月次請求書-INV001-20240115.PDF
            #     随時請求書-INV002-20240115.PDF
            parts = file_name.replace('.PDF', '').replace('.pdf', '').split('-')
            
            if len(parts) < 3:
                return JsonResponse({
                    'status': 'error',
                    'message': 'ファイル名の形式が不正です'
                }, status=400)
            
            doc_type_str = parts[0]
            invoice_number = parts[1]
            invoice_date_str = parts[2]
            
            # 文書種別判定
            if '月次請求書' in doc_type_str:
                document_type = 'monthly'
            elif '随時請求書' in doc_type_str:
                document_type = 'adhoc'
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': '文書種別が不正です'
                }, status=400)
            
            # 請求日をパース
            try:
                invoice_date = datetime.strptime(invoice_date_str, '%Y%m%d').date()
            except:
                return JsonResponse({
                    'status': 'error',
                    'message': '請求日の形式が不正です'
                }, status=400)
            
            # 年度・月を取得
            year = str(invoice_date.year)
            month = str(invoice_date.month).zfill(2)
            
            # フォルダを取得または作成
            cabinet = Cabinet.objects.first()
            if not cabinet:
                return JsonResponse({
                    'status': 'error',
                    'message': 'キャビネットが存在しません'
                }, status=500)
            
            # 取引先フォルダ
            client_folder, _ = Folder.objects.get_or_create(
                cabinet=cabinet,
                name=client_code,
                folder_type='client',
                client_code=client_code
            )
            
            # 年度フォルダ
            year_folder, _ = Folder.objects.get_or_create(
                cabinet=cabinet,
                parent=client_folder,
                name=year,
                folder_type='year',
                client_code=client_code,
                year=year
            )
            
            # 月フォルダ
            month_folder, _ = Folder.objects.get_or_create(
                cabinet=cabinet,
                parent=year_folder,
                name=month,
                folder_type='month',
                client_code=client_code,
                year=year,
                month=month
            )
            
            # 既存文書の版数管理
            existing_docs = Document.objects.filter(
                folder=month_folder,
                file_name=file_name
            ).order_by('-version')
            
            if existing_docs.exists():
                # 既存文書がある場合、版数をインクリメント
                latest_doc = existing_docs.first()
                new_version = latest_doc.version + 1
                
                # 既存文書のis_latestをFalseに更新
                Document.objects.filter(
                    folder=month_folder,
                    file_name=file_name
                ).update(is_latest=False)
            else:
                new_version = 1
            
            # ファイルサイズチェック（20MB）
            if pdf_file.size > Document.MAX_FILE_SIZE:
                return JsonResponse({
                    'status': 'error',
                    'message': f'ファイルサイズが上限（20MB）を超えています'
                }, status=400)
            
            # ファイルデータを読み込み
            file_data = pdf_file.read()
            
            # 暗号化処理
            if encrypt_flag:
                # 取引先のグループパスワードを取得
                group = Group.objects.filter(client_code=client_code).first()
                
                if group and group.group_password:
                    try:
                        # PDFを暗号化
                        file_data = encrypt_pdf(file_data, group.group_password)
                    except Exception as e:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'PDF暗号化エラー: {str(e)}'
                        }, status=500)
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'取引先コード {client_code} のグループパスワードが設定されていません'
                    }, status=400)
            
            # 新規文書を登録
            document = Document.objects.create(
                folder=month_folder,
                file_name=file_name,
                document_type=document_type,
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                version=new_version,
                is_latest=True,
                file_data=file_data,
                file_size=len(file_data),  # 暗号化後のサイズ
                encrypt_flag=encrypt_flag,
                uploaded_by=request.user
            )
            
            # メール通知
            self._send_notification_email(client_code, file_name)
            
            return JsonResponse({
                'status': 'success',
                'message': '文書を登録しました',
                'document_id': document.id,
                'version': new_version
            })
        
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    def _send_notification_email(self, client_code, file_name):
        """請求書登録通知メール送信"""
        try:
            group = Group.objects.filter(client_code=client_code).first()
            if not group:
                return
            
            # グループメンバーのメールアドレスを取得
            members = group.members.all()
            recipient_list = [member.user.email for member in members]
            
            if recipient_list:
                subject = '【WEB請求書システム】新しい請求書が登録されました'
                message = f'''
請求書が登録されました。

ファイル名: {file_name}

以下のURLからログインして確認してください。
http://localhost:8000/login/

よろしくお願いいたします。
'''
                
                send_mail(subject, message, 'noreply@webseikyu.local', recipient_list)
        
        except Exception as e:
            # メール送信エラーはログのみ
            print(f'メール送信エラー: {e}')
