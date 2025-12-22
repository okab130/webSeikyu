from django.core.management.base import BaseCommand
from django.utils import timezone
from documents.models import (
    User, Cabinet, Folder, Client, Group, GroupMember,
    FolderPermission, Document, RegistrationRequest,
    RegistrationRequestContact
)
from datetime import date, timedelta
import os
from django.core.files.base import ContentFile


class Command(BaseCommand):
    help = 'テスト用データを投入します'

    def handle(self, *args, **options):
        self.stdout.write('テストデータの投入を開始します...')

        # 既存データのクリア
        self.stdout.write('既存データをクリアしています...')
        Document.objects.all().delete()
        FolderPermission.objects.all().delete()
        Folder.objects.all().delete()
        GroupMember.objects.all().delete()
        Group.objects.all().delete()
        RegistrationRequestContact.objects.all().delete()
        RegistrationRequest.objects.all().delete()
        Client.objects.all().delete()
        Cabinet.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        # 1. 管理者ユーザーの作成
        self.stdout.write('管理者ユーザーを作成しています...')
        admin_user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'user_type': 'admin',
                'full_name': '管理者',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'  管理者作成: {admin_user.email}'))

        # スタッフユーザー
        staff_user = User.objects.create(
            email='staff@example.com',
            user_type='staff',
            full_name='スタッフ太郎',
            is_staff=True,
        )
        staff_user.set_password('staff123')
        staff_user.save()
        self.stdout.write(self.style.SUCCESS(f'  スタッフ作成: {staff_user.email}'))

        # APIユーザー
        api_user = User.objects.create(
            email='api@example.com',
            user_type='api',
            full_name='請求書発行システム',
        )
        api_user.set_password('api123')
        api_user.save()
        self.stdout.write(self.style.SUCCESS(f'  APIユーザー作成: {api_user.email}'))

        # 2. キャビネットの作成
        self.stdout.write('\nキャビネットを作成しています...')
        cabinet = Cabinet.objects.create(
            name='請求書キャビネット',
            description='取引先別の請求書を管理するキャビネット'
        )
        self.stdout.write(self.style.SUCCESS(f'  キャビネット作成: {cabinet.name}'))

        # ルートフォルダの作成
        root_folder = Folder.objects.create(
            cabinet=cabinet,
            name='請求書',
            folder_type='root'
        )
        self.stdout.write(self.style.SUCCESS(f'  ルートフォルダ作成: {root_folder.name}'))

        # 3. 取引先とグループの作成
        self.stdout.write('\n取引先とグループを作成しています...')
        
        clients_data = [
            {
                'code': '00001',
                'name': '株式会社サンプル商事',
                'address': '東京都渋谷区渋谷1-1-1',
                'password': 'sample2024',
                'contacts': [
                    {'name': '山田太郎', 'email': 'yamada@sample.co.jp', 'password': 'yamada123'},
                    {'name': '佐藤花子', 'email': 'sato@sample.co.jp', 'password': 'sato123'},
                ]
            },
            {
                'code': '00002',
                'name': 'テスト株式会社',
                'address': '大阪府大阪市北区梅田2-2-2',
                'password': 'test2024',
                'contacts': [
                    {'name': '鈴木一郎', 'email': 'suzuki@test.co.jp', 'password': 'suzuki123'},
                ]
            },
            {
                'code': '00003',
                'name': '有限会社デモ企業',
                'address': '福岡県福岡市中央区天神3-3-3',
                'password': 'demo2024',
                'contacts': [
                    {'name': '田中次郎', 'email': 'tanaka@demo.co.jp', 'password': 'tanaka123'},
                    {'name': '伊藤美咲', 'email': 'ito@demo.co.jp', 'password': 'ito123'},
                    {'name': '高橋健太', 'email': 'takahashi@demo.co.jp', 'password': 'takahashi123'},
                ]
            },
        ]

        for client_data in clients_data:
            # 取引先作成
            client = Client.objects.create(
                client_code=client_data['code'],
                client_name=client_data['name'],
                address=client_data['address']
            )
            self.stdout.write(self.style.SUCCESS(f'  取引先作成: {client}'))

            # グループ作成
            group = Group.objects.create(
                group_id=client_data['code'],
                name=client_data['name'],
                client_code=client_data['code'],
                group_password=client_data['password']
            )
            self.stdout.write(self.style.SUCCESS(f'    グループ作成: {group.group_id}'))

            # 取引先フォルダ作成
            client_folder = Folder.objects.create(
                cabinet=cabinet,
                parent=root_folder,
                name=client_data['name'],
                folder_type='client',
                client_code=client_data['code']
            )

            # フォルダ権限設定
            FolderPermission.objects.create(
                folder=client_folder,
                group=group,
                permission_type='read'
            )

            # 年度フォルダ作成（2024年）
            year_folder = Folder.objects.create(
                cabinet=cabinet,
                parent=client_folder,
                name='2024年',
                folder_type='year',
                client_code=client_data['code'],
                year='2024'
            )

            # 月フォルダ作成（10月、11月、12月）
            for month_num in [10, 11, 12]:
                month_str = str(month_num).zfill(2)
                month_folder = Folder.objects.create(
                    cabinet=cabinet,
                    parent=year_folder,
                    name=f'{month_num}月',
                    folder_type='month',
                    client_code=client_data['code'],
                    year='2024',
                    month=month_str
                )

                # 各月にサンプル請求書を作成
                invoice_date = date(2024, month_num, 1)
                invoice_number = f'INV-{client_data["code"]}-{invoice_date.strftime("%Y%m")}-001'
                
                # ダミーPDFファイル（実際のPDFではなく、テキストファイル）
                dummy_content = f'サンプル請求書\n取引先: {client_data["name"]}\n請求書番号: {invoice_number}\n請求日: {invoice_date}'
                file_data_bytes = dummy_content.encode('utf-8')
                
                document = Document.objects.create(
                    folder=month_folder,
                    file_name=f'{invoice_number}.pdf',
                    document_type='monthly',
                    invoice_number=invoice_number,
                    invoice_date=invoice_date,
                    version=1,
                    is_latest=True,
                    file_data=file_data_bytes,
                    file_size=len(file_data_bytes),
                    encrypt_flag=True,
                    uploaded_by=api_user
                )
                self.stdout.write(self.style.SUCCESS(f'      文書作成: {document.file_name}'))

            # 担当者ユーザー作成
            for contact in client_data['contacts']:
                user = User.objects.create(
                    email=contact['email'],
                    user_type='client',
                    client_code=client_data['code'],
                    full_name=contact['name']
                )
                user.set_password(contact['password'])
                user.save()

                # グループメンバーに追加
                GroupMember.objects.create(
                    group=group,
                    user=user
                )
                self.stdout.write(self.style.SUCCESS(f'    担当者作成: {user.full_name} ({user.email})'))

        # 4. 新規登録依頼の作成（pending状態）
        self.stdout.write('\n新規登録依頼を作成しています...')
        reg_request = RegistrationRequest.objects.create(
            client_code='00004',
            client_name='新規株式会社',
            address='東京都新宿区新宿4-4-4',
            group_password='shinki2024',
            status='pending'
        )
        
        # 担当者を3名登録
        contacts_data = [
            {'name': '新規太郎', 'email': 'shinki1@shinki.co.jp', 'password': 'shinki1pass'},
            {'name': '新規花子', 'email': 'shinki2@shinki.co.jp', 'password': 'shinki2pass'},
            {'name': '新規次郎', 'email': 'shinki3@shinki.co.jp', 'password': 'shinki3pass'},
        ]
        
        for i, contact_data in enumerate(contacts_data, 1):
            RegistrationRequestContact.objects.create(
                request=reg_request,
                contact_name=contact_data['name'],
                contact_email=contact_data['email'],
                contact_password=contact_data['password'],
                contact_order=i
            )
        
        self.stdout.write(self.style.SUCCESS(f'  新規登録依頼作成: {reg_request.client_code} - {reg_request.client_name}'))

        # 5. データサマリー
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('テストデータの投入が完了しました！'))
        self.stdout.write('='*50)
        self.stdout.write(f'\n【作成されたデータ】')
        self.stdout.write(f'  キャビネット: {Cabinet.objects.count()}件')
        self.stdout.write(f'  フォルダ: {Folder.objects.count()}件')
        self.stdout.write(f'  取引先: {Client.objects.count()}件')
        self.stdout.write(f'  グループ: {Group.objects.count()}件')
        self.stdout.write(f'  ユーザー: {User.objects.count()}件')
        self.stdout.write(f'  グループメンバー: {GroupMember.objects.count()}件')
        self.stdout.write(f'  文書: {Document.objects.count()}件')
        self.stdout.write(f'  新規登録依頼: {RegistrationRequest.objects.count()}件')

        self.stdout.write(f'\n【ログイン情報】')
        self.stdout.write(f'  管理者: admin@example.com / admin123')
        self.stdout.write(f'  スタッフ: staff@example.com / staff123')
        self.stdout.write(f'  APIユーザー: api@example.com / api123')
        self.stdout.write(f'\n  取引先担当者:')
        self.stdout.write(f'    山田太郎: yamada@sample.co.jp / yamada123')
        self.stdout.write(f'    佐藤花子: sato@sample.co.jp / sato123')
        self.stdout.write(f'    鈴木一郎: suzuki@test.co.jp / suzuki123')
        self.stdout.write(f'    田中次郎: tanaka@demo.co.jp / tanaka123')
        self.stdout.write(f'    伊藤美咲: ito@demo.co.jp / ito123')
        self.stdout.write(f'    高橋健太: takahashi@demo.co.jp / takahashi123')
