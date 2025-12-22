from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """カスタムユーザーマネージャー"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('メールアドレスは必須です')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('スーパーユーザーはis_staff=Trueである必要があります')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('スーパーユーザーはis_superuser=Trueである必要があります')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """利用者モデル"""
    
    USER_TYPE_CHOICES = [
        ('admin', '管理者'),
        ('staff', 'スタッフ'),
        ('client', '取引先'),
        ('api', 'API'),
    ]
    
    email = models.EmailField('メールアドレス', unique=True)
    user_type = models.CharField('ユーザー種別', max_length=20, choices=USER_TYPE_CHOICES)
    client_code = models.CharField('取引先コード', max_length=5, blank=True, null=True, db_index=True)
    full_name = models.CharField('氏名', max_length=100, blank=True)
    is_active = models.BooleanField('有効フラグ', default=True)
    is_staff = models.BooleanField('スタッフフラグ', default=False)
    date_joined = models.DateTimeField('登録日時', default=timezone.now)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = '利用者'
        verbose_name_plural = '利用者'
    
    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"


class Cabinet(models.Model):
    """キャビネットモデル"""
    
    name = models.CharField('キャビネット名', max_length=200, unique=True)
    description = models.TextField('説明', blank=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        db_table = 'cabinets'
        verbose_name = 'キャビネット'
        verbose_name_plural = 'キャビネット'
    
    def __str__(self):
        return self.name


class Folder(models.Model):
    """フォルダモデル"""
    
    FOLDER_TYPE_CHOICES = [
        ('root', 'ルート'),
        ('client', '取引先'),
        ('year', '年度'),
        ('month', '月'),
    ]
    
    cabinet = models.ForeignKey(Cabinet, on_delete=models.CASCADE, related_name='folders', verbose_name='キャビネット')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True, blank=True, verbose_name='親フォルダ')
    name = models.CharField('フォルダ名', max_length=100)
    folder_type = models.CharField('フォルダ種別', max_length=20, choices=FOLDER_TYPE_CHOICES)
    client_code = models.CharField('取引先コード', max_length=5, blank=True, null=True, db_index=True)
    year = models.CharField('年度', max_length=4, blank=True, null=True)
    month = models.CharField('月', max_length=2, blank=True, null=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        db_table = 'folders'
        verbose_name = 'フォルダ'
        verbose_name_plural = 'フォルダ'
        indexes = [
            models.Index(fields=['client_code']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_folder_type_display()})"


class Client(models.Model):
    """取引先モデル"""
    
    client_code = models.CharField('取引先コード', max_length=5, unique=True, db_index=True)
    client_name = models.CharField('取引先名', max_length=200)
    address = models.TextField('住所', blank=True)
    is_active = models.BooleanField('有効フラグ', default=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        db_table = 'clients'
        verbose_name = '取引先'
        verbose_name_plural = '取引先'
    
    def __str__(self):
        return f"{self.client_code} - {self.client_name}"


class Group(models.Model):
    """グループモデル"""
    
    group_id = models.CharField('グループID', max_length=5, unique=True, db_index=True)
    name = models.CharField('グループ名', max_length=200)
    client_code = models.CharField('取引先コード', max_length=5, db_index=True)
    group_password = models.CharField('グループパスワード', max_length=128)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        db_table = 'groups'
        verbose_name = 'グループ'
        verbose_name_plural = 'グループ'
    
    def __str__(self):
        return f"{self.group_id} - {self.name}"


class GroupMember(models.Model):
    """グループメンバーモデル"""
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members', verbose_name='グループ')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships', verbose_name='利用者')
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    
    class Meta:
        db_table = 'group_members'
        verbose_name = 'グループメンバー'
        verbose_name_plural = 'グループメンバー'
        unique_together = ('group', 'user')
    
    def __str__(self):
        return f"{self.group.group_id} - {self.user.email}"


class FolderPermission(models.Model):
    """フォルダ権限モデル"""
    
    PERMISSION_TYPE_CHOICES = [
        ('read', '参照権限'),
        ('admin', '管理者権限'),
    ]
    
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='permissions', verbose_name='フォルダ')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='folder_permissions', verbose_name='グループ')
    permission_type = models.CharField('権限種別', max_length=20, choices=PERMISSION_TYPE_CHOICES)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        db_table = 'folder_permissions'
        verbose_name = 'フォルダ権限'
        verbose_name_plural = 'フォルダ権限'
        unique_together = ('folder', 'group')
    
    def __str__(self):
        return f"{self.folder.name} - {self.group.group_id} ({self.get_permission_type_display()})"


class Document(models.Model):
    """文書モデル"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('monthly', '月次請求書'),
        ('adhoc', '随時請求書'),
    ]
    
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
    
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='documents', verbose_name='フォルダ')
    file_name = models.CharField('ファイル名', max_length=255, db_index=True)
    document_type = models.CharField('文書種別', max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    invoice_number = models.CharField('請求書番号', max_length=50)
    invoice_date = models.DateField('請求日')
    version = models.IntegerField('版数', default=1)
    is_latest = models.BooleanField('最新版フラグ', default=True, db_index=True)
    file_data = models.BinaryField('ファイルデータ', null=True, blank=True)
    file_size = models.BigIntegerField('ファイルサイズ')
    encrypt_flag = models.BooleanField('暗号化フラグ', default=False)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_documents', verbose_name='登録者')
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        db_table = 'documents'
        verbose_name = '文書'
        verbose_name_plural = '文書'
        indexes = [
            models.Index(fields=['file_name']),
            models.Index(fields=['is_latest']),
        ]
    
    def __str__(self):
        return f"{self.file_name} (v{self.version})"


class RegistrationRequest(models.Model):
    """新規登録依頼モデル"""
    
    STATUS_CHOICES = [
        ('pending', '未承認'),
        ('approved', '承認済み'),
        ('rejected', '却下'),
    ]
    
    client_code = models.CharField('取引先コード', max_length=5, db_index=True)
    client_name = models.CharField('取引先名', max_length=200)
    address = models.TextField('住所')
    group_password = models.CharField('グループパスワード', max_length=128)
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    rejection_reason = models.TextField('却下理由', blank=True)
    requested_at = models.DateTimeField('依頼日時', auto_now_add=True)
    processed_at = models.DateTimeField('処理日時', null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_registrations', verbose_name='処理者')
    
    class Meta:
        db_table = 'registration_requests'
        verbose_name = '新規登録依頼'
        verbose_name_plural = '新規登録依頼'
        indexes = [
            models.Index(fields=['client_code']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.client_code} - {self.client_name} ({self.get_status_display()})"


class RegistrationRequestContact(models.Model):
    """新規登録依頼の担当者モデル"""
    
    request = models.ForeignKey(RegistrationRequest, on_delete=models.CASCADE, related_name='contacts', verbose_name='登録依頼')
    contact_name = models.CharField('担当者名', max_length=100)
    contact_email = models.EmailField('担当者メール')
    contact_password = models.CharField('担当者パスワード', max_length=128)
    contact_order = models.IntegerField('順序', default=1)
    
    class Meta:
        db_table = 'registration_request_contacts'
        verbose_name = '新規登録依頼担当者'
        verbose_name_plural = '新規登録依頼担当者'
        ordering = ['contact_order']
    
    def __str__(self):
        return f"{self.request.client_code} - {self.contact_name}"


class ChangeRequest(models.Model):
    """変更依頼モデル"""
    
    STATUS_CHOICES = [
        ('pending', '未承認'),
        ('approved', '承認済み'),
        ('rejected', '却下'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='change_requests', verbose_name='取引先')
    client_name = models.CharField('変更後取引先名', max_length=200, null=True, blank=True)
    address = models.TextField('変更後住所', null=True, blank=True)
    group_password = models.CharField('変更後グループパスワード', max_length=128, null=True, blank=True)
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    rejection_reason = models.TextField('却下理由', blank=True)
    requested_at = models.DateTimeField('依頼日時', auto_now_add=True)
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='requested_changes', verbose_name='依頼者')
    processed_at = models.DateTimeField('処理日時', null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_changes', verbose_name='処理者')
    
    class Meta:
        db_table = 'change_requests'
        verbose_name = '変更依頼'
        verbose_name_plural = '変更依頼'
        indexes = [
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.client.client_code} - {self.get_status_display()}"


class ChangeRequestContact(models.Model):
    """変更依頼の担当者モデル"""
    
    ACTION_TYPE_CHOICES = [
        ('add', '追加'),
        ('update', '更新'),
        ('delete', '削除'),
    ]
    
    request = models.ForeignKey(ChangeRequest, on_delete=models.CASCADE, related_name='contact_changes', verbose_name='変更依頼')
    action_type = models.CharField('操作種別', max_length=20, choices=ACTION_TYPE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contact_changes', verbose_name='対象ユーザー')
    contact_name = models.CharField('担当者名', max_length=100, null=True, blank=True)
    contact_email = models.EmailField('担当者メール', null=True, blank=True)
    contact_password = models.CharField('担当者パスワード', max_length=128, null=True, blank=True)
    
    class Meta:
        db_table = 'change_request_contacts'
        verbose_name = '変更依頼担当者'
        verbose_name_plural = '変更依頼担当者'
    
    def __str__(self):
        return f"{self.request.client.client_code} - {self.get_action_type_display()}"

