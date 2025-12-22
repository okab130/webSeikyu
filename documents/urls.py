from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # 公開画面
    path('', views.IndexView.as_view(), name='index'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.ClientRegisterView.as_view(), name='client_register'),
    path('register/confirm/', views.RegisterConfirmView.as_view(), name='register_confirm'),
    
    # 取引先画面
    path('client/dashboard/', views.ClientDashboardView.as_view(), name='client_dashboard'),
    path('client/documents/', views.ClientDocumentListView.as_view(), name='client_documents'),
    path('client/documents/download/<int:document_id>/', views.ClientDocumentDownloadView.as_view(), name='client_document_download'),
    path('client/profile/', views.ClientProfileView.as_view(), name='client_profile'),
    path('client/profile/edit/', views.ClientProfileEditView.as_view(), name='client_profile_edit'),
    path('client/manual/', views.ClientManualView.as_view(), name='client_manual'),
    
    # スタッフ画面
    path('staff/dashboard/', views.StaffDashboardView.as_view(), name='staff_dashboard'),
    path('staff/manual/', views.StaffManualView.as_view(), name='staff_manual'),
    path('staff/registration-requests/', views.RegistrationRequestListView.as_view(), name='registration_request_list'),
    path('staff/registration-requests/<int:request_id>/', views.RegistrationRequestDetailView.as_view(), name='registration_request_detail'),
    path('staff/registration-requests/<int:request_id>/approve/', views.RegistrationRequestApproveView.as_view(), name='registration_request_approve'),
    path('staff/registration-requests/<int:request_id>/reject/', views.RegistrationRequestRejectView.as_view(), name='registration_request_reject'),
    path('staff/change-requests/', views.ChangeRequestListView.as_view(), name='change_request_list'),
    path('staff/change-requests/<int:request_id>/', views.ChangeRequestDetailView.as_view(), name='change_request_detail'),
    path('staff/change-requests/<int:request_id>/approve/', views.ChangeRequestApproveView.as_view(), name='change_request_approve'),
    path('staff/change-requests/<int:request_id>/reject/', views.ChangeRequestRejectView.as_view(), name='change_request_reject'),
    path('staff/clients/', views.StaffClientListView.as_view(), name='staff_client_list'),
    path('staff/clients/<int:client_id>/', views.StaffClientDetailView.as_view(), name='staff_client_detail'),
    path('staff/documents/search/', views.StaffDocumentSearchView.as_view(), name='staff_document_search'),
    path('staff/documents/upload/', views.StaffDocumentUploadView.as_view(), name='staff_document_upload'),
    path('staff/documents/<int:document_id>/', views.StaffDocumentDetailView.as_view(), name='staff_document_detail'),
    path('staff/documents/<int:document_id>/delete/', views.StaffDocumentDeleteView.as_view(), name='staff_document_delete'),
    path('staff/documents/download/<int:document_id>/', views.StaffDocumentDownloadView.as_view(), name='staff_document_download'),
    
    # API
    path('api/login/', views.APILoginView.as_view(), name='api_login'),
    path('api/logout/', views.APILogoutView.as_view(), name='api_logout'),
    path('api/documents/upload/', views.APIDocumentUploadView.as_view(), name='api_document_upload'),
]
