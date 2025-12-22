# URL設計

## URLルーティング設計

### 公開画面（認証不要）
- `/` - トップページ（ログイン画面へリダイレクト）
- `/login/` - ログイン画面
- `/register/` - 新規取引先登録画面
- `/register/confirm/` - 新規登録完了画面

### 取引先画面（認証必要：client）
- `/client/dashboard/` - 取引先ダッシュボード（請求書一覧・フォルダツリー）
- `/client/documents/` - 文書一覧
- `/client/documents/download/<int:document_id>/` - 文書ダウンロード
- `/client/profile/` - 登録情報表示
- `/client/profile/edit/` - 登録情報変更画面

### スタッフ画面（認証必要：staff）
- `/staff/dashboard/` - スタッフダッシュボード
- `/staff/registration-requests/` - 新規登録依頼一覧
- `/staff/registration-requests/<int:request_id>/` - 新規登録依頼詳細
- `/staff/registration-requests/<int:request_id>/approve/` - 承認処理
- `/staff/registration-requests/<int:request_id>/reject/` - 却下処理
- `/staff/change-requests/` - 変更依頼一覧
- `/staff/change-requests/<int:request_id>/` - 変更依頼詳細
- `/staff/change-requests/<int:request_id>/approve/` - 承認処理
- `/staff/change-requests/<int:request_id>/reject/` - 却下処理
- `/staff/clients/` - 取引先一覧
- `/staff/clients/<int:client_id>/` - 取引先詳細
- `/staff/documents/search/` - 文書検索
- `/staff/documents/<int:document_id>/` - 文書詳細
- `/staff/documents/<int:document_id>/delete/` - 文書削除
- `/staff/documents/download/<int:document_id>/` - 文書ダウンロード

### API（認証必要：api）
- `/api/login/` - API認証ログイン
- `/api/logout/` - API認証ログアウト
- `/api/documents/upload/` - 請求書PDF登録API

### 共通
- `/logout/` - ログアウト
