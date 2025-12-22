# Djangoモデル設計（models.py）

## 設計方針
- データモデル中心のアプローチ
- Djangoのベストプラクティスに従う（Fat models, thin views）
- 正規化とデータ整合性を重視
- 将来の拡張性を考慮

## モデル一覧

### 1. Cabinet（キャビネット）
文書管理の最上位階層

| フィールド名 | 型 | 説明 | 制約 |
|------------|-----|------|------|
| id | BigAutoField | 主キー | PK, Auto |
| name | CharField(200) | キャビネット名 | unique, not null |
| description | TextField | 説明 | blank=True |
| created_at | DateTimeField | 作成日時 | auto_now_add |
| updated_at | DateTimeField | 更新日時 | auto_now |

**備考**:
- セットアップ時に「請求書キャビネット」を1つ作成
- 将来的に複数キャビネット対応も可能


### 2. Folder（フォルダ）
階層構造を持つフォルダ管理

| フィールド名 | 型 | 説明 | 制約 |
|------------|-----|------|------|
| id | BigAutoField | 主キー | PK, Auto |
| cabinet | ForeignKey(Cabinet) | 所属キャビネット | CASCADE, not null |
| parent | ForeignKey(Folder) | 親フォルダ | CASCADE, null=True |
| name | CharField(100) | フォルダ名 | not null |
| folder_type | CharField(20) | フォルダ種別 | choices=['root', 'client', 'year', 'month'] |
| client_code | CharField(5) | 取引先コード | null=True, db_index |
| year | CharField(4) | 年度 | null=True |
| month | CharField(2) | 月 | null=True |
| created_at | DateTimeField | 作成日時 | auto_now_add |
| updated_at | DateTimeField | 更新日時 | auto_now |

**備考**:
- folder_type: root（請求書キャビネット直下）、client（取引先）、year（年度）、month（月）
- 階層構造: Cabinet → root → client → year → month
- client_codeにインデックス設定（検索高速化）


### 3. Group（グループ）
アクセス権限管理用のグループ

| フィールド名 | 型 | 説明 | 制約 |
|------------|-----|------|------|
| id | BigAutoField | 主キー | PK, Auto |
| group_id | CharField(5) | グループID | unique, not null, db_index |
| name | CharField(200) | グループ名 | not null |
| client_code | CharField(5) | 取引先コード | not null, db_index |
| group_password | CharField(128) | グループパスワード | not null |
| created_at | DateTimeField | 作成日時 | auto_now_add |
| updated_at | DateTimeField | 更新日時 | auto_now |

**備考**:
- group_id = client_code（同一の値）
- group_passwordはPDF暗号化用（平文保存でOK、ログインパスワードとは別）
- 即時反映のため、変更依頼は不要


### 4. User（利用者）
Django標準のAbstractUserを拡張

| フィールド名 | 型 | 説明 | 制約 |
|------------|-----|------|------|
| id | BigAutoField | 主キー | PK, Auto |
| email | EmailField | メールアドレス | unique, not null |
| password | CharField(128) | パスワード（ハッシュ化） | not null |
| user_type | CharField(20) | ユーザー種別 | choices=['admin', 'staff', 'client', 'api'] |
| client_code | CharField(5) | 取引先コード | null=True, db_index |
| full_name | CharField(100) | 氏名 | blank=True |
| is_active | BooleanField | 有効フラグ | default=True |
| is_staff | BooleanField | スタッフフラグ | default=False |
| is_superuser | BooleanField | 管理者フラグ | default=False |
| date_joined | DateTimeField | 登録日時 | auto_now_add |
| last_login | DateTimeField | 最終ログイン | null=True |

**備考**:
- AbstractUserを継承してカスタマイズ
- USERNAME_FIELD = 'email'（メールアドレスでログイン）
- user_type: admin（管理者）、staff（スタッフ）、client（取引先）、api（請求書発行システム）
- パスワードはDjangoの標準機能でハッシュ化


### 5. GroupMember（グループメンバー）
グループと利用者の多対多関連

| フィールド名 | 型 | 説明 | 制約 |
|------------|-----|------|------|
| id | BigAutoField | 主キー | PK, Auto |
| group | ForeignKey(Group) | グループ | CASCADE, not null |
| user | ForeignKey(User) | 利用者 | CASCADE, not null |
| created_at | DateTimeField | 作成日時 | auto_now_add |

**備考**:
- unique_together = ('group', 'user')
- 取引先の担当者（最大3名）をグループに登録


### 6. FolderPermission（フォルダ権限）
フォルダに対するグループのアクセス権限

| フィールド名 | 型 | 説明 | 制約 |
|------------|-----|------|------|
| id | BigAutoField | 主キー | PK, Auto |
| folder | ForeignKey(Folder) | フォルダ | CASCADE, not null |
| group | ForeignKey(Group) | グループ | CASCADE, not null |
| permission_type | CharField(20) | 権限種別 | choices=['read', 'admin'] |
| created_at | DateTimeField | 作成日時 | auto_now_add |
| updated_at | DateTimeField | 更新日時 | auto_now |

**備考**:
- unique_together = ('folder', 'group')
- permission_type: read（参照権限）、admin（管理者権限）
- 権限継承ロジックはビュー側で実装


### 7. Document（文書）
請求書PDFの管理

| フィールド名 | 型 | 説明 | 制約 |
|------------|-----|------|------|
| id | BigAutoField | 主キー | PK, Auto |
| folder | ForeignKey(Folder) | 所属フォルダ | CASCADE, not null |
| file_name | CharField(255) | ファイル名 | not null, db_index |
| document_type | CharField(20) | 文書種別 | choices=['monthly', 'adhoc'] |
| invoice_number | CharField(50) | 請求書番号 | not null |
| invoice_date | DateField | 請求日 | not null |
| version | IntegerField | 版数 | default=1 |
| is_latest | BooleanField | 最新版フラグ | default=True, db_index |
| file_path | FileField | ファイルパス | not null |
| file_size | BigIntegerField | ファイルサイズ | not null |
| encrypt_flag | BooleanField | 暗号化フラグ | default=False |
| uploaded_by | ForeignKey(User) | 登録者 | SET_NULL, null=True |
| created_at | DateTimeField | 作成日時 | auto_now_add |
| updated_at | DateTimeField | 更新日時 | auto_now |

**備考**:
- document_type: monthly（月次請求書）、adhoc（随時請求書）
- 同一file_nameで版数管理
- is_latestで最新版を高速検索
- file_pathはMediaフォルダ配下に保存
- encrypt_flagがTrueの場合、ダウンロード時にグループパスワードで暗号化


### 8. Client（取引先）
取引先マスタ情報

| フィールド名 | 型 | 説明 | 制約 |
|------------|-----|------|------|
| id | BigAutoField | 主キー | PK, Auto |
| client_code | CharField(5) | 取引先コード | unique, not null, db_index |
| client_name | CharField(200) | 取引先名 | not null |
| address | TextField | 住所 | blank=True |
| is_active | BooleanField | 有効フラグ | default=True |
| created_at | DateTimeField | 作成日時 | auto_now_add |
| updated_at | DateTimeField | 更新日時 | auto_now |

**備考**:
- 新規登録承認時に作成
- 取引先コードは5桁数字、システム内でユニーク


### 9. RegistrationRequest（新規登録依頼）
取引先の新規登録申請

| フィールド名 | 型 | 説明 | 制約 |
|------------|-----|------|------|
| id | BigAutoField | 主キー | PK, Auto |
| client_code | CharField(5) | 取引先コード | not null, db_index |
| client_name | CharField(200) | 取引先名 | not null |
| address | TextField | 住所 | not null |
| group_password | CharField(128) | グループパスワード | not null |
| status | CharField(20) | ステータス | choices=['pending', 'approved', 'rejected'] |
| rejection_reason | TextField | 却下理由 | blank=True |
| requested_at | DateTimeField | 依頼日時 | auto_now_add |
| processed_at | DateTimeField | 処理日時 | null=True |
| processed_by | ForeignKey(User) | 処理者 | SET_NULL, null=True |

**備考**:
- status: pending（未承認）、approved（承認済み）、rejected（却下）
- 担当者情報は別テーブル（RegistrationRequestContact）で管理


### 10. RegistrationRequestContact（新規登録依頼の担当者）
新規登録申請の担当者情報（最大3名）

| フィールド名 | 型 | 説明 | 制約 |
|------------|-----|------|------|
| id | BigAutoField | 主キー | PK, Auto |
| request | ForeignKey(RegistrationRequest) | 登録依頼 | CASCADE, not null |
| contact_name | CharField(100) | 担当者名 | not null |
| contact_email | EmailField | 担当者メール | not null |
| contact_password | CharField(128) | 担当者パスワード | not null |
| contact_order | IntegerField | 順序 | default=1 |

**備考**:
- contact_order: 1～3（最大3名）
- contact_passwordは平文で一時保存、承認時にハッシュ化してUserテーブルへ


### 11. ChangeRequest（変更依頼）
取引先情報の変更申請

| フィールド名 | 型 | 説明 | 制約 |
|------------|-----|------|------|
| id | BigAutoField | 主キー | PK, Auto |
| client | ForeignKey(Client) | 取引先 | CASCADE, not null |
| client_name | CharField(200) | 変更後取引先名 | null=True |
| address | TextField | 変更後住所 | null=True |
| group_password | CharField(128) | 変更後グループPW | null=True |
| status | CharField(20) | ステータス | choices=['pending', 'approved', 'rejected'] |
| rejection_reason | TextField | 却下理由 | blank=True |
| requested_at | DateTimeField | 依頼日時 | auto_now_add |
| requested_by | ForeignKey(User) | 依頼者 | SET_NULL, null=True |
| processed_at | DateTimeField | 処理日時 | null=True |
| processed_by | ForeignKey(User) | 処理者 | SET_NULL, null=True |

**備考**:
- 変更項目のみnullでない値を設定
- 担当者変更は別テーブル（ChangeRequestContact）で管理


### 12. ChangeRequestContact（変更依頼の担当者）
変更申請の担当者情報

| フィールド名 | 型 | 説明 | 制約 |
|------------|-----|------|------|
| id | BigAutoField | 主キー | PK, Auto |
| request | ForeignKey(ChangeRequest) | 変更依頼 | CASCADE, not null |
| action_type | CharField(20) | 操作種別 | choices=['add', 'update', 'delete'] |
| user | ForeignKey(User) | 対象ユーザー | SET_NULL, null=True |
| contact_name | CharField(100) | 担当者名 | null=True |
| contact_email | EmailField | 担当者メール | null=True |
| contact_password | CharField(128) | 担当者パスワード | null=True |

**備考**:
- action_type: add（追加）、update（更新）、delete（削除）
- 更新の場合はuserで対象を特定


## モデル関連図

```
Cabinet (1) -----> (N) Folder
                      |
                      +---> (1) parent (自己参照)
                      |
                      +---> (N) FolderPermission -----> (1) Group
                      |
                      +---> (N) Document

Client (1) -----> (1) Group
           |           |
           |           +---> (N) GroupMember -----> (1) User
           |
           +---> (N) RegistrationRequest -----> (N) RegistrationRequestContact
           |
           +---> (N) ChangeRequest -----> (N) ChangeRequestContact

User
  +---> user_type: admin / staff / client / api
```

## インデックス設計
パフォーマンス最適化のため以下にインデックスを設定：
- Folder.client_code
- Group.group_id, client_code
- User.email, client_code
- Document.file_name, is_latest
- Client.client_code
- RegistrationRequest.client_code, status
- ChangeRequest.status

## 次のステップ
1. モデル設計のレビュー・確認
2. models.pyの実装
3. マイグレーションファイル生成
4. 初期データ投入（請求書キャビネット作成）
