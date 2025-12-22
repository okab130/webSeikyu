# ビュー設計

## 設計方針
- クラスベースビュー（CBV）を使用
- ミックスインで認証・権限チェックを実装
- Fat models, thin views の原則に従う
- トランザクション管理は@transaction.atomicを使用

## ビュー分類

### 1. 公開ビュー（views_public.py）
- IndexView - トップページ
- LoginView - ログイン
- LogoutView - ログアウト
- ClientRegisterView - 新規登録
- RegisterConfirmView - 登録完了

### 2. 取引先ビュー（views_client.py）
- ClientDashboardView - ダッシュボード
- ClientDocumentListView - 文書一覧
- ClientDocumentDownloadView - 文書ダウンロード
- ClientProfileView - プロフィール表示
- ClientProfileEditView - プロフィール編集

### 3. スタッフビュー（views_staff.py）
- StaffDashboardView - ダッシュボード
- RegistrationRequestListView - 新規登録依頼一覧
- RegistrationRequestDetailView - 新規登録依頼詳細
- RegistrationRequestApproveView - 承認処理
- RegistrationRequestRejectView - 却下処理
- ChangeRequestListView - 変更依頼一覧
- ChangeRequestDetailView - 変更依頼詳細
- ChangeRequestApproveView - 承認処理
- ChangeRequestRejectView - 却下処理
- StaffClientListView - 取引先一覧
- StaffClientDetailView - 取引先詳細
- StaffDocumentSearchView - 文書検索
- StaffDocumentDetailView - 文書詳細
- StaffDocumentDeleteView - 文書削除
- StaffDocumentDownloadView - 文書ダウンロード

### 4. APIビュー（views_api.py）
- APILoginView - API認証
- APILogoutView - APIログアウト
- APIDocumentUploadView - 文書アップロードAPI

### 5. ミックスイン（mixins.py）
- ClientRequiredMixin - 取引先ユーザー必須
- StaffRequiredMixin - スタッフユーザー必須
- APIRequiredMixin - APIユーザー必須
