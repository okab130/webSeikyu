from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User, Cabinet, Folder, Client, Group, GroupMember,
    FolderPermission, Document, RegistrationRequest, RegistrationRequestContact,
    ChangeRequest, ChangeRequestContact
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """利用者管理"""
    list_display = ['email', 'user_type', 'client_code', 'full_name', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_active', 'is_staff']
    search_fields = ['email', 'full_name', 'client_code']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('個人情報', {'fields': ('full_name', 'user_type', 'client_code')}),
        ('権限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要な日付', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'user_type', 'password1', 'password2'),
        }),
    )


@admin.register(Cabinet)
class CabinetAdmin(admin.ModelAdmin):
    """キャビネット管理"""
    list_display = ['name', 'description', 'created_at', 'updated_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    """フォルダ管理"""
    list_display = ['name', 'folder_type', 'client_code', 'year', 'month', 'cabinet', 'parent', 'created_at']
    list_filter = ['folder_type', 'cabinet']
    search_fields = ['name', 'client_code']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['parent']


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """取引先管理"""
    list_display = ['client_code', 'client_name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['client_code', 'client_name', 'address']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """グループ管理"""
    list_display = ['group_id', 'name', 'client_code', 'created_at']
    search_fields = ['group_id', 'name', 'client_code']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    """グループメンバー管理"""
    list_display = ['group', 'user', 'created_at']
    list_filter = ['group']
    search_fields = ['group__group_id', 'user__email']
    readonly_fields = ['created_at']
    raw_id_fields = ['group', 'user']


@admin.register(FolderPermission)
class FolderPermissionAdmin(admin.ModelAdmin):
    """フォルダ権限管理"""
    list_display = ['folder', 'group', 'permission_type', 'created_at']
    list_filter = ['permission_type']
    search_fields = ['folder__name', 'group__group_id']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['folder', 'group']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """文書管理"""
    list_display = ['file_name', 'document_type', 'version', 'is_latest', 'encrypt_flag', 'uploaded_by', 'created_at']
    list_filter = ['document_type', 'is_latest', 'encrypt_flag', 'created_at']
    search_fields = ['file_name', 'invoice_number']
    readonly_fields = ['created_at', 'updated_at', 'file_size']
    raw_id_fields = ['folder', 'uploaded_by']
    date_hierarchy = 'invoice_date'


class RegistrationRequestContactInline(admin.TabularInline):
    """新規登録依頼の担当者インライン"""
    model = RegistrationRequestContact
    extra = 0
    fields = ['contact_order', 'contact_name', 'contact_email', 'contact_password']


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    """新規登録依頼管理"""
    list_display = ['client_code', 'client_name', 'status', 'requested_at', 'processed_at', 'processed_by']
    list_filter = ['status', 'requested_at']
    search_fields = ['client_code', 'client_name']
    readonly_fields = ['requested_at', 'processed_at']
    inlines = [RegistrationRequestContactInline]
    
    fieldsets = (
        ('取引先情報', {
            'fields': ('client_code', 'client_name', 'address', 'group_password')
        }),
        ('ステータス', {
            'fields': ('status', 'rejection_reason', 'requested_at', 'processed_at', 'processed_by')
        }),
    )


class ChangeRequestContactInline(admin.TabularInline):
    """変更依頼の担当者インライン"""
    model = ChangeRequestContact
    extra = 0
    fields = ['action_type', 'user', 'contact_name', 'contact_email', 'contact_password']
    raw_id_fields = ['user']


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    """変更依頼管理"""
    list_display = ['client', 'status', 'requested_at', 'requested_by', 'processed_at', 'processed_by']
    list_filter = ['status', 'requested_at']
    search_fields = ['client__client_code', 'client__client_name']
    readonly_fields = ['requested_at', 'processed_at']
    raw_id_fields = ['client', 'requested_by', 'processed_by']
    inlines = [ChangeRequestContactInline]
    
    fieldsets = (
        ('取引先', {
            'fields': ('client',)
        }),
        ('変更内容', {
            'fields': ('client_name', 'address', 'group_password')
        }),
        ('ステータス', {
            'fields': ('status', 'rejection_reason', 'requested_at', 'requested_by', 'processed_at', 'processed_by')
        }),
    )
