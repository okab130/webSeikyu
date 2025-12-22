from django.views.generic import TemplateView, ListView, DetailView, FormView, View
from django.shortcuts import get_object_or_404, redirect
from django.http import FileResponse, Http404
from django.db.models import Q
from .mixins import ClientRequiredMixin
from .models import Document, Folder, Client, Group, ChangeRequest, ChangeRequestContact
from .forms import ClientProfileEditForm
import os


class ClientManualView(ClientRequiredMixin, TemplateView):
    """取引先向けマニュアル"""
    template_name = 'documents/client/manual.html'


class ClientDashboardView(ClientRequiredMixin, TemplateView):
    """取引先ダッシュボード"""
    template_name = 'documents/client/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # 取引先のルートフォルダを取得
        client_folder = Folder.objects.filter(
            client_code=user.client_code,
            folder_type='client'
        ).first()
        
        # フォルダツリーを構築
        if client_folder:
            context['root_folder'] = client_folder
            context['folders'] = self._build_folder_tree(client_folder)
        
        return context
    
    def _build_folder_tree(self, parent_folder):
        """フォルダツリーを再帰的に構築"""
        folders = []
        children = Folder.objects.filter(parent=parent_folder).order_by('year', 'month')
        
        for child in children:
            folder_data = {
                'folder': child,
                'documents': Document.objects.filter(folder=child, is_latest=True).order_by('-created_at'),
                'children': self._build_folder_tree(child)
            }
            folders.append(folder_data)
        
        return folders


class ClientDocumentListView(ClientRequiredMixin, ListView):
    """取引先文書一覧"""
    template_name = 'documents/client/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        # 取引先コードに基づいてフォルダを取得
        folders = Folder.objects.filter(client_code=user.client_code)
        # 最新版の文書のみ取得
        return Document.objects.filter(folder__in=folders, is_latest=True).order_by('-created_at')


class ClientDocumentDownloadView(ClientRequiredMixin, View):
    """取引先文書ダウンロード"""
    
    def get(self, request, document_id):
        from django.http import HttpResponse
        
        document = get_object_or_404(Document, id=document_id, is_latest=True)
        user = request.user
        
        # 権限チェック：自分の取引先の文書のみ
        if document.folder.client_code != user.client_code:
            raise Http404('この文書にアクセスする権限がありません')
        
        # ファイルデータが存在するか確認
        if not document.file_data:
            raise Http404('ファイルが見つかりません')
        
        # ファイルデータを取得（アップロード時に既に暗号化済み）
        file_data = bytes(document.file_data)
        
        # ファイルダウンロード
        response = HttpResponse(file_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{document.file_name}"'
        response['Content-Length'] = document.file_size
        return response


class ClientProfileView(ClientRequiredMixin, DetailView):
    """取引先プロフィール表示"""
    template_name = 'documents/client/profile.html'
    context_object_name = 'client'
    
    def get_object(self):
        user = self.request.user
        return get_object_or_404(Client, client_code=user.client_code)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.object
        
        # グループ情報を取得
        context['group'] = Group.objects.filter(client_code=client.client_code).first()
        
        # 担当者一覧を取得
        from .models import User
        context['users'] = User.objects.filter(client_code=client.client_code, user_type='client')
        
        return context


class ClientProfileEditView(ClientRequiredMixin, FormView):
    """取引先プロフィール編集"""
    template_name = 'documents/client/profile_edit.html'
    form_class = ClientProfileEditForm
    
    def get_success_url(self):
        return '/client/profile/'
    
    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user
        client = get_object_or_404(Client, client_code=user.client_code)
        
        initial['client_name'] = client.client_name
        initial['address'] = client.address
        
        # 担当者情報の初期値設定
        from .models import User
        users = User.objects.filter(client_code=user.client_code, user_type='client').order_by('id')
        
        for i, contact_user in enumerate(users, 1):
            if i <= 3:
                initial[f'contact{i}_name'] = contact_user.full_name
                initial[f'contact{i}_email'] = contact_user.email
        
        return initial
    
    def form_valid(self, form):
        from django.db import transaction
        from django.utils import timezone
        
        user = self.request.user
        client = get_object_or_404(Client, client_code=user.client_code)
        
        with transaction.atomic():
            # グループパスワードは即時反映
            group_password = form.cleaned_data.get('group_password')
            if group_password:
                group = Group.objects.filter(client_code=client.client_code).first()
                if group:
                    group.group_password = group_password
                    group.save()
            
            # 基本情報の変更があるか確認
            client_name_changed = form.cleaned_data['client_name'] != client.client_name
            address_changed = form.cleaned_data['address'] != client.address
            
            # 変更依頼を作成（基本情報の変更がある場合のみ）
            if client_name_changed or address_changed or form.cleaned_data.get('contact1_change') or form.cleaned_data.get('contact2_change') or form.cleaned_data.get('contact3_change'):
                change_request = ChangeRequest.objects.create(
                    client=client,
                    client_name=form.cleaned_data['client_name'] if client_name_changed else None,
                    address=form.cleaned_data['address'] if address_changed else None,
                    status='pending',
                    requested_by=user
                )
                
                # 担当者変更の処理
                from .models import User
                existing_users = list(User.objects.filter(client_code=client.client_code, user_type='client').order_by('id'))
                
                for i in range(1, 4):
                    change_flag = form.cleaned_data.get(f'contact{i}_change')
                    delete_flag = form.cleaned_data.get(f'contact{i}_delete')
                    
                    if change_flag:
                        contact_name = form.cleaned_data.get(f'contact{i}_name')
                        contact_email = form.cleaned_data.get(f'contact{i}_email')
                        contact_password = form.cleaned_data.get(f'contact{i}_password')
                        
                        if contact_name and contact_email:
                            # 既存ユーザーがいる場合は更新、いない場合は追加
                            if i <= len(existing_users):
                                ChangeRequestContact.objects.create(
                                    request=change_request,
                                    action_type='update',
                                    user=existing_users[i-1],
                                    contact_name=contact_name,
                                    contact_email=contact_email,
                                    contact_password=contact_password if contact_password else None
                                )
                            else:
                                ChangeRequestContact.objects.create(
                                    request=change_request,
                                    action_type='add',
                                    contact_name=contact_name,
                                    contact_email=contact_email,
                                    contact_password=contact_password
                                )
                    
                    elif delete_flag and i <= len(existing_users):
                        ChangeRequestContact.objects.create(
                            request=change_request,
                            action_type='delete',
                            user=existing_users[i-1]
                        )
        
        return super().form_valid(form)
