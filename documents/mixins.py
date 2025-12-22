from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class ClientRequiredMixin(LoginRequiredMixin):
    """取引先ユーザー専用ミックスイン"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.user_type != 'client':
            raise PermissionDenied('この画面は取引先ユーザーのみアクセスできます')
        
        return super().dispatch(request, *args, **kwargs)


class StaffRequiredMixin(LoginRequiredMixin):
    """スタッフユーザー専用ミックスイン"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.user_type not in ['staff', 'admin']:
            raise PermissionDenied('この画面はスタッフのみアクセスできます')
        
        return super().dispatch(request, *args, **kwargs)


class APIRequiredMixin:
    """APIユーザー専用ミックスイン"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.user_type != 'api':
            raise PermissionDenied('このAPIはAPIユーザーのみアクセスできます')
        
        return super().dispatch(request, *args, **kwargs)
