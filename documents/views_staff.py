from django.views.generic import TemplateView, ListView, DetailView, FormView, View
from django.shortcuts import get_object_or_404, redirect
from django.http import FileResponse, Http404, JsonResponse, HttpResponse
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from .mixins import StaffRequiredMixin
from .models import (
    RegistrationRequest, RegistrationRequestContact, ChangeRequest, ChangeRequestContact,
    Client, Group, GroupMember, Folder, FolderPermission, Document, User, Cabinet
)
from .forms import RegistrationRequestRejectForm, ChangeRequestRejectForm, DocumentSearchForm, DocumentUploadForm
from .pdf_utils import encrypt_pdf
import os
from datetime import datetime


class StaffManualView(StaffRequiredMixin, TemplateView):
    """管理者向けマニュアル"""
    template_name = 'documents/staff/manual.html'


class StaffDashboardView(StaffRequiredMixin, TemplateView):
    """スタッフダッシュボード"""
    template_name = 'documents/staff/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 未承認の新規登録依頼
        context['pending_registrations'] = RegistrationRequest.objects.filter(
            status='pending'
        ).order_by('-requested_at')[:10]
        
        # 未承認の変更依頼
        context['pending_changes'] = ChangeRequest.objects.filter(
            status='pending'
        ).order_by('-requested_at')[:10]
        
        # 承認済み・却下済みの履歴
        context['recent_registrations'] = RegistrationRequest.objects.filter(
            status__in=['approved', 'rejected']
        ).order_by('-processed_at')[:5]
        
        context['recent_changes'] = ChangeRequest.objects.filter(
            status__in=['approved', 'rejected']
        ).order_by('-processed_at')[:5]
        
        return context


class RegistrationRequestListView(StaffRequiredMixin, ListView):
    """新規登録依頼一覧"""
    template_name = 'documents/staff/registration_request_list.html'
    context_object_name = 'requests'
    paginate_by = 20
    
    def get_queryset(self):
        return RegistrationRequest.objects.all().order_by('-requested_at')


class RegistrationRequestDetailView(StaffRequiredMixin, DetailView):
    """新規登録依頼詳細"""
    template_name = 'documents/staff/registration_request_detail.html'
    context_object_name = 'request'
    pk_url_kwarg = 'request_id'
    model = RegistrationRequest


class RegistrationRequestApproveView(StaffRequiredMixin, View):
    """新規登録依頼承認処理"""
    
    @transaction.atomic
    def post(self, request, request_id):
        reg_request = get_object_or_404(RegistrationRequest, id=request_id, status='pending')
        
        # 取引先を作成
        client = Client.objects.create(
            client_code=reg_request.client_code,
            client_name=reg_request.client_name,
            address=reg_request.address
        )
        
        # グループを作成
        group = Group.objects.create(
            group_id=reg_request.client_code,
            name=f'{reg_request.client_name}グループ',
            client_code=reg_request.client_code,
            group_password=reg_request.group_password
        )
        
        # フォルダを作成
        cabinet = Cabinet.objects.first()
        client_folder = Folder.objects.create(
            cabinet=cabinet,
            name=reg_request.client_code,
            folder_type='client',
            client_code=reg_request.client_code
        )
        
        # フォルダ権限を設定
        FolderPermission.objects.create(
            folder=client_folder,
            group=group,
            permission_type='read'
        )
        
        # 担当者（利用者）を作成
        contacts = reg_request.contacts.all()
        for contact in contacts:
            user = User.objects.create_user(
                email=contact.contact_email,
                password=contact.contact_password,
                user_type='client',
                client_code=reg_request.client_code,
                full_name=contact.contact_name
            )
            
            # グループメンバーに追加
            GroupMember.objects.create(group=group, user=user)
        
        # 登録依頼のステータスを更新
        reg_request.status = 'approved'
        reg_request.processed_at = timezone.now()
        reg_request.processed_by = request.user
        reg_request.save()
        
        # メール通知
        self._send_approval_email(reg_request)
        
        return redirect('documents:staff_dashboard')
    
    def _send_approval_email(self, reg_request):
        """承認メール送信"""
        subject = '【WEB請求書システム】新規登録が承認されました'
        message = f'''
{reg_request.client_name} 様

WEB請求書システムへの新規登録申請が承認されました。

以下のURLからログインしてください。
http://localhost:8000/login/

取引先コード: {reg_request.client_code}

よろしくお願いいたします。
'''
        
        # 全担当者にメール送信
        recipient_list = [contact.contact_email for contact in reg_request.contacts.all()]
        send_mail(subject, message, 'noreply@webseikyu.local', recipient_list)


class RegistrationRequestRejectView(StaffRequiredMixin, FormView):
    """新規登録依頼却下処理"""
    template_name = 'documents/staff/registration_request_reject.html'
    form_class = RegistrationRequestRejectForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_id = self.kwargs['request_id']
        context['request'] = get_object_or_404(RegistrationRequest, id=request_id)
        return context
    
    @transaction.atomic
    def form_valid(self, form):
        request_id = self.kwargs['request_id']
        reg_request = get_object_or_404(RegistrationRequest, id=request_id, status='pending')
        
        # 却下処理
        reg_request.status = 'rejected'
        reg_request.rejection_reason = form.cleaned_data['rejection_reason']
        reg_request.processed_at = timezone.now()
        reg_request.processed_by = self.request.user
        reg_request.save()
        
        # メール通知
        self._send_rejection_email(reg_request)
        
        return redirect('documents:staff_dashboard')
    
    def _send_rejection_email(self, reg_request):
        """却下メール送信"""
        subject = '【WEB請求書システム】新規登録申請が却下されました'
        message = f'''
{reg_request.client_name} 様

WEB請求書システムへの新規登録申請が却下されました。

却下理由:
{reg_request.rejection_reason}

ご不明な点がございましたら、お問い合わせください。
'''
        
        recipient_list = [contact.contact_email for contact in reg_request.contacts.all()]
        send_mail(subject, message, 'noreply@webseikyu.local', recipient_list)


class ChangeRequestListView(StaffRequiredMixin, ListView):
    """変更依頼一覧"""
    template_name = 'documents/staff/change_request_list.html'
    context_object_name = 'requests'
    paginate_by = 20
    
    def get_queryset(self):
        return ChangeRequest.objects.all().order_by('-requested_at')


class ChangeRequestDetailView(StaffRequiredMixin, DetailView):
    """変更依頼詳細"""
    template_name = 'documents/staff/change_request_detail.html'
    context_object_name = 'request'
    pk_url_kwarg = 'request_id'
    model = ChangeRequest


class ChangeRequestApproveView(StaffRequiredMixin, View):
    """変更依頼承認処理"""
    
    @transaction.atomic
    def post(self, request, request_id):
        change_request = get_object_or_404(ChangeRequest, id=request_id, status='pending')
        client = change_request.client
        
        # 取引先情報を更新
        if change_request.client_name:
            client.client_name = change_request.client_name
        if change_request.address:
            client.address = change_request.address
        client.save()
        
        # グループパスワード更新
        if change_request.group_password:
            group = Group.objects.filter(client_code=client.client_code).first()
            if group:
                group.group_password = change_request.group_password
                group.save()
        
        # 担当者変更処理
        group = Group.objects.filter(client_code=client.client_code).first()
        for contact_change in change_request.contact_changes.all():
            if contact_change.action_type == 'add':
                # 担当者追加
                user = User.objects.create_user(
                    email=contact_change.contact_email,
                    password=contact_change.contact_password,
                    user_type='client',
                    client_code=client.client_code,
                    full_name=contact_change.contact_name
                )
                if group:
                    GroupMember.objects.create(group=group, user=user)
            
            elif contact_change.action_type == 'update':
                # 担当者更新
                if contact_change.user:
                    user = contact_change.user
                    if contact_change.contact_name:
                        user.full_name = contact_change.contact_name
                    if contact_change.contact_email:
                        user.email = contact_change.contact_email
                    if contact_change.contact_password:
                        user.set_password(contact_change.contact_password)
                    user.save()
            
            elif contact_change.action_type == 'delete':
                # 担当者削除
                if contact_change.user:
                    user = contact_change.user
                    if group:
                        GroupMember.objects.filter(group=group, user=user).delete()
                    user.is_active = False
                    user.save()
        
        # 変更依頼のステータスを更新
        change_request.status = 'approved'
        change_request.processed_at = timezone.now()
        change_request.processed_by = request.user
        change_request.save()
        
        # メール通知
        self._send_approval_email(change_request)
        
        return redirect('documents:staff_dashboard')
    
    def _send_approval_email(self, change_request):
        """承認メール送信"""
        subject = '【WEB請求書システム】変更申請が承認されました'
        message = f'''
{change_request.client.client_name} 様

登録情報の変更申請が承認されました。

変更内容が反映されています。

よろしくお願いいたします。
'''
        
        # 取引先の担当者全員にメール送信
        users = User.objects.filter(
            client_code=change_request.client.client_code,
            user_type='client',
            is_active=True
        )
        recipient_list = [user.email for user in users]
        if recipient_list:
            send_mail(subject, message, 'noreply@webseikyu.local', recipient_list)


class ChangeRequestRejectView(StaffRequiredMixin, FormView):
    """変更依頼却下処理"""
    template_name = 'documents/staff/change_request_reject.html'
    form_class = ChangeRequestRejectForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_id = self.kwargs['request_id']
        context['request'] = get_object_or_404(ChangeRequest, id=request_id)
        return context
    
    @transaction.atomic
    def form_valid(self, form):
        request_id = self.kwargs['request_id']
        change_request = get_object_or_404(ChangeRequest, id=request_id, status='pending')
        
        # 却下処理
        change_request.status = 'rejected'
        change_request.rejection_reason = form.cleaned_data['rejection_reason']
        change_request.processed_at = timezone.now()
        change_request.processed_by = self.request.user
        change_request.save()
        
        # メール通知
        self._send_rejection_email(change_request)
        
        return redirect('documents:staff_dashboard')
    
    def _send_rejection_email(self, change_request):
        """却下メール送信"""
        subject = '【WEB請求書システム】変更申請が却下されました'
        message = f'''
{change_request.client.client_name} 様

登録情報の変更申請が却下されました。

却下理由:
{change_request.rejection_reason}

ご不明な点がございましたら、お問い合わせください。
'''
        
        # 取引先の担当者全員にメール送信
        users = User.objects.filter(
            client_code=change_request.client.client_code,
            user_type='client',
            is_active=True
        )
        recipient_list = [user.email for user in users]
        if recipient_list:
            send_mail(subject, message, 'noreply@webseikyu.local', recipient_list)


class StaffClientListView(StaffRequiredMixin, ListView):
    """取引先一覧"""
    template_name = 'documents/staff/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20
    model = Client


class StaffClientDetailView(StaffRequiredMixin, DetailView):
    """取引先詳細"""
    template_name = 'documents/staff/client_detail.html'
    context_object_name = 'client'
    pk_url_kwarg = 'client_id'
    model = Client
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.object
        
        # 関連データを取得
        context['users'] = User.objects.filter(client_code=client.client_code)
        context['group'] = Group.objects.filter(client_code=client.client_code).first()
        context['folders'] = Folder.objects.filter(client_code=client.client_code)
        
        # 文書数を計算
        document_count = Document.objects.filter(
            folder__client_code=client.client_code
        ).count()
        context['document_count'] = document_count
        
        return context


class StaffDocumentSearchView(StaffRequiredMixin, FormView):
    """文書検索"""
    template_name = 'documents/staff/document_search.html'
    form_class = DocumentSearchForm
    
    def get(self, request, *args, **kwargs):
        """GETリクエスト処理"""
        form = self.get_form()
        
        # 検索パラメータがあれば検索を実行
        if request.GET:
            client_code = request.GET.get('client_code', '').strip()
            year = request.GET.get('year', '').strip()
            month = request.GET.get('month', '').strip()
            
            # 文書検索の基本クエリ
            documents = Document.objects.all()
            
            # 取引先コードで絞り込み（指定された場合のみ）
            if client_code:
                folders = Folder.objects.filter(client_code=client_code)
                
                if year:
                    folders = folders.filter(year=year)
                if month:
                    folders = folders.filter(month=month)
                
                documents = documents.filter(folder__in=folders)
            else:
                # 取引先コードが指定されていない場合、年度・月で絞り込み
                if year:
                    documents = documents.filter(folder__year=year)
                if month:
                    documents = documents.filter(folder__month=month)
            
            # 作成日時の降順でソート
            documents = documents.order_by('-created_at')
            
            context = self.get_context_data(form=form)
            context['documents'] = documents
            return self.render_to_response(context)
        
        # 検索パラメータがない場合は空のフォームを表示
        return self.render_to_response(self.get_context_data(form=form))


class StaffDocumentDetailView(StaffRequiredMixin, DetailView):
    """文書詳細"""
    template_name = 'documents/staff/document_detail.html'
    context_object_name = 'document'
    pk_url_kwarg = 'document_id'
    model = Document


class StaffDocumentDeleteView(StaffRequiredMixin, View):
    """文書削除"""
    
    @transaction.atomic
    def post(self, request, document_id):
        document = get_object_or_404(Document, id=document_id)
        
        # 全版数を削除
        file_name = document.file_name
        folder = document.folder
        
        all_versions = Document.objects.filter(folder=folder, file_name=file_name)
        
        # 文書を削除（バイナリデータはDB内なのでファイル削除不要）
        all_versions.delete()
        
        return redirect('documents:staff_document_search')


class StaffDocumentUploadView(StaffRequiredMixin, FormView):
    """文書アップロード"""
    template_name = 'documents/staff/document_upload.html'
    form_class = DocumentUploadForm
    success_url = '/staff/documents/search/'
    
    @transaction.atomic
    def form_valid(self, form):
        client_code = form.cleaned_data['client_code']
        document_type = form.cleaned_data['document_type']
        invoice_number = form.cleaned_data['invoice_number']
        invoice_date = form.cleaned_data['invoice_date']
        pdf_file = form.cleaned_data['file']
        encrypt_flag = form.cleaned_data['encrypt_flag']
        
        # キャビネット取得
        cabinet = Cabinet.objects.first()
        if not cabinet:
            form.add_error(None, 'キャビネットが存在しません')
            return self.form_invalid(form)
        
        # 年度・月を取得
        year = str(invoice_date.year)
        month = str(invoice_date.month).zfill(2)
        
        # フォルダを取得または作成
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
            name=f"{month}月",
            folder_type='month',
            client_code=client_code,
            year=year,
            month=month
        )
        
        # ファイル名生成
        file_name = pdf_file.name
        
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
        
        # ファイルデータを読み込み
        file_data = pdf_file.read()
        
        # 暗号化処理
        if encrypt_flag:
            # 取引先のグループパスワードを取得
            try:
                client = Client.objects.get(client_code=client_code)
                group = Group.objects.filter(client_code=client_code).first()
                
                if group and group.group_password:
                    # PDFを暗号化
                    file_data = encrypt_pdf(file_data, group.group_password)
                else:
                    form.add_error(None, f'取引先コード {client_code} のグループパスワードが設定されていません')
                    return self.form_invalid(form)
            except Client.DoesNotExist:
                form.add_error('client_code', f'取引先コード {client_code} が見つかりません')
                return self.form_invalid(form)
            except Exception as e:
                form.add_error(None, f'PDF暗号化エラー: {str(e)}')
                return self.form_invalid(form)
        
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
            uploaded_by=self.request.user
        )
        
        return super().form_valid(form)


class StaffDocumentDownloadView(StaffRequiredMixin, View):
    """文書ダウンロード"""
    
    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id)
        
        # ファイルデータが存在するか確認
        if not document.file_data:
            raise Http404('ファイルが見つかりません')
        
        # ファイルダウンロード
        file_data = bytes(document.file_data)
        response = HttpResponse(file_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{document.file_name}"'
        response['Content-Length'] = document.file_size
        return response
