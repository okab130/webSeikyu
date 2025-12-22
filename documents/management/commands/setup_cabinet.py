from django.core.management.base import BaseCommand
from documents.models import Cabinet


class Command(BaseCommand):
    help = '請求書キャビネットを作成する初期セットアップコマンド'

    def handle(self, *args, **options):
        cabinet_name = '請求書キャビネット'
        
        if Cabinet.objects.filter(name=cabinet_name).exists():
            self.stdout.write(self.style.WARNING(f'キャビネット「{cabinet_name}」は既に存在します'))
        else:
            cabinet = Cabinet.objects.create(
                name=cabinet_name,
                description='取引先の請求書を管理するキャビネット'
            )
            self.stdout.write(self.style.SUCCESS(f'キャビネット「{cabinet_name}」を作成しました (ID: {cabinet.id})'))
