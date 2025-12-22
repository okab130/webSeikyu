from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import RegistrationRequest, RegistrationRequestContact, ChangeRequest, ChangeRequestContact, Client, User


class LoginForm(AuthenticationForm):
    """ログインフォーム"""
    username = forms.EmailField(
        label='メールアドレス',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'メールアドレス',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='パスワード',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'パスワード'
        })
    )


class ClientRegisterForm(forms.ModelForm):
    """取引先新規登録フォーム"""
    
    group_password_confirm = forms.CharField(
        label='グループパスワード（確認）',
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='PDFファイルを開く際に必要なパスワードです。'
    )
    
    # 担当者1
    contact1_name = forms.CharField(label='担当者1 氏名', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    contact1_email = forms.EmailField(label='担当者1 メールアドレス', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    contact1_password = forms.CharField(label='担当者1 パスワード', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    # 担当者2（任意）
    contact2_name = forms.CharField(label='担当者2 氏名', max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    contact2_email = forms.EmailField(label='担当者2 メールアドレス', required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    contact2_password = forms.CharField(label='担当者2 パスワード', required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    # 担当者3（任意）
    contact3_name = forms.CharField(label='担当者3 氏名', max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    contact3_email = forms.EmailField(label='担当者3 メールアドレス', required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    contact3_password = forms.CharField(label='担当者3 パスワード', required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = RegistrationRequest
        fields = ['client_code', 'client_name', 'address', 'group_password']
        widgets = {
            'client_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '5桁の数字'}),
            'client_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'group_password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'client_code': '5桁の数字を入力してください',
            'group_password': 'ダウンロードしたPDFファイルを開く際に必要なパスワードです',
        }
    
    def clean_client_code(self):
        client_code = self.cleaned_data['client_code']
        
        # 5桁の数字チェック
        if not client_code.isdigit() or len(client_code) != 5:
            raise forms.ValidationError('取引先コードは5桁の数字で入力してください')
        
        # 重複チェック
        if Client.objects.filter(client_code=client_code).exists():
            raise forms.ValidationError('この取引先コードは既に登録されています')
        
        # 登録依頼中チェック
        if RegistrationRequest.objects.filter(client_code=client_code, status='pending').exists():
            raise forms.ValidationError('この取引先コードは現在登録申請中です')
        
        return client_code
    
    def clean(self):
        cleaned_data = super().clean()
        group_password = cleaned_data.get('group_password')
        group_password_confirm = cleaned_data.get('group_password_confirm')
        
        # グループパスワード確認
        if group_password and group_password_confirm:
            if group_password != group_password_confirm:
                raise forms.ValidationError('グループパスワードが一致しません')
        
        # 担当者1は必須
        if not cleaned_data.get('contact1_name') or not cleaned_data.get('contact1_email') or not cleaned_data.get('contact1_password'):
            raise forms.ValidationError('担当者1は必須です')
        
        # 担当者2の整合性チェック
        contact2_fields = [cleaned_data.get('contact2_name'), cleaned_data.get('contact2_email'), cleaned_data.get('contact2_password')]
        if any(contact2_fields) and not all(contact2_fields):
            raise forms.ValidationError('担当者2を登録する場合は、全ての項目を入力してください')
        
        # 担当者3の整合性チェック
        contact3_fields = [cleaned_data.get('contact3_name'), cleaned_data.get('contact3_email'), cleaned_data.get('contact3_password')]
        if any(contact3_fields) and not all(contact3_fields):
            raise forms.ValidationError('担当者3を登録する場合は、全ての項目を入力してください')
        
        # メールアドレス重複チェック
        emails = []
        if cleaned_data.get('contact1_email'):
            emails.append(cleaned_data.get('contact1_email'))
        if cleaned_data.get('contact2_email'):
            emails.append(cleaned_data.get('contact2_email'))
        if cleaned_data.get('contact3_email'):
            emails.append(cleaned_data.get('contact3_email'))
        
        if len(emails) != len(set(emails)):
            raise forms.ValidationError('担当者のメールアドレスが重複しています')
        
        # 既存ユーザーとの重複チェック
        for email in emails:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(f'メールアドレス「{email}」は既に登録されています')
        
        return cleaned_data


class ClientProfileEditForm(forms.Form):
    """取引先情報変更フォーム"""
    
    client_name = forms.CharField(label='取引先名', max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(label='住所', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    group_password = forms.CharField(label='グループパスワード', max_length=128, required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    # 担当者変更フラグ
    contact1_change = forms.BooleanField(label='担当者1を変更', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    contact1_name = forms.CharField(label='担当者1 氏名', max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    contact1_email = forms.EmailField(label='担当者1 メールアドレス', required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    contact1_password = forms.CharField(label='担当者1 パスワード', required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    contact2_change = forms.BooleanField(label='担当者2を変更', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    contact2_name = forms.CharField(label='担当者2 氏名', max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    contact2_email = forms.EmailField(label='担当者2 メールアドレス', required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    contact2_password = forms.CharField(label='担当者2 パスワード', required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    contact2_delete = forms.BooleanField(label='担当者2を削除', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    contact3_change = forms.BooleanField(label='担当者3を変更', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    contact3_name = forms.CharField(label='担当者3 氏名', max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    contact3_email = forms.EmailField(label='担当者3 メールアドレス', required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    contact3_password = forms.CharField(label='担当者3 パスワード', required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    contact3_delete = forms.BooleanField(label='担当者3を削除', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))


class RegistrationRequestRejectForm(forms.Form):
    """新規登録依頼却下フォーム"""
    rejection_reason = forms.CharField(
        label='却下理由',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=True
    )


class ChangeRequestRejectForm(forms.Form):
    """変更依頼却下フォーム"""
    rejection_reason = forms.CharField(
        label='却下理由',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=True
    )


class DocumentSearchForm(forms.Form):
    """文書検索フォーム"""
    client_code = forms.CharField(
        label='取引先コード',
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '5桁の数字（任意）'})
    )
    year = forms.CharField(
        label='年度',
        max_length=4,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYY'})
    )
    month = forms.CharField(
        label='月',
        max_length=2,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'MM'})
    )


class DocumentUploadForm(forms.Form):
    """文書アップロードフォーム"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('monthly', '月次請求書'),
        ('adhoc', '随時請求書'),
    ]
    
    client_code = forms.CharField(
        label='取引先コード',
        max_length=5,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '5桁の数字'
        })
    )
    
    document_type = forms.ChoiceField(
        label='文書種別',
        choices=DOCUMENT_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    invoice_number = forms.CharField(
        label='請求書番号',
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '例: INV-00001-202412-001'
        })
    )
    
    invoice_date = forms.DateField(
        label='請求日',
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    file = forms.FileField(
        label='PDFファイル',
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,application/pdf'
        })
    )
    
    encrypt_flag = forms.BooleanField(
        label='暗号化する',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean_file(self):
        """ファイルバリデーション"""
        file = self.cleaned_data.get('file')
        
        if file:
            # ファイルサイズチェック（20MB）
            if file.size > 20 * 1024 * 1024:
                raise forms.ValidationError('ファイルサイズは20MB以下にしてください。')
            
            # ファイル拡張子チェック
            if not file.name.lower().endswith('.pdf'):
                raise forms.ValidationError('PDFファイルのみアップロード可能です。')
        
        return file
    
    def clean_client_code(self):
        """取引先コードバリデーション"""
        client_code = self.cleaned_data.get('client_code')
        
        if client_code:
            # 5桁の数字チェック
            if not client_code.isdigit() or len(client_code) != 5:
                raise forms.ValidationError('取引先コードは5桁の数字で入力してください。')
        
        return client_code
