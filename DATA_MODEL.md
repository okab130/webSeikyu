# データモデル詳細設計書

**バージョン**: 1.0  
**作成日**: 2024-12-21  
**最終更新日**: 2024-12-21

---

## 目次

1. [データモデル概要](#1-データモデル概要)
2. [テーブル定義](#2-テーブル定義)
3. [ER図](#3-er図)
4. [インデックス設計](#4-インデックス設計)
5. [制約定義](#5-制約定義)

---

## 1. データモデル概要

### 1.1 データモデルの構成

WEB請求書システムのデータモデルは以下の9つのテーブルで構成されています。

| テーブル名 | 論理名 | 説明 |
|----------|--------|------|
| documents_user | ユーザー | システム利用者 |
| documents_client | 取引先 | 取引先マスタ |
| documents_group | グループ | 取引先単位のグループ |
| documents_groupmember | グループメンバー | 担当者情報 |
| documents_cabinet | キャビネット | 文書管理の最上位階層 |
| documents_folder | フォルダ | 文書を格納する階層 |
| documents_document | 文書 | 請求書PDFデータ |
| documents_folderpermission | フォルダ権限 | フォルダへのアクセス権 |
| documents_registrationrequest | 新規登録依頼 | 取引先新規登録申請 |
| documents_registrationrequestcontact | 登録依頼担当者 | 新規登録時の担当者 |
| documents_changerequest | 変更依頼 | プロフィール変更申請 |
| documents_changerequestcontact | 変更依頼担当者 | 変更申請の担当者情報 |

### 1.2 データモデルの特徴

- **文書データのDB保存**: PDFファイルはBinaryField（バイナリ形式）でDB内に保存
- **版数管理**: 同一ファイル名の文書は版数（version）で管理
- **階層構造**: キャビネット → フォルダ（取引先 → 年度 → 月）→ 文書
- **承認ワークフロー**: 登録依頼・変更依頼はステータス管理
- **論理削除**: is_active フラグによる論理削除

---

## 2. テーブル定義

### 2.1 documents_user (ユーザー)

システムを利用するユーザーの情報を管理します。

| 物理名 | 論理名 | 型 | PK | FK | NULL | デフォルト | 説明 |
|-------|--------|---|----|----|------|-----------|------|
| id | ID | BIGINT | ○ | - | × | AUTO | 主キー |
| email | メールアドレス | VARCHAR(254) | - | - | × | - | ログインID（一意） |
| password | パスワード | VARCHAR(128) | - | - | × | - | ハッシュ化済み |
| user_type | ユーザー種別 | VARCHAR(20) | - | - | × | - | admin/staff/client/api |
| client_code | 取引先コード | VARCHAR(5) | - | - | ○ | - | clientの場合必須 |
| full_name | 氏名 | VARCHAR(100) | - | - | ○ | '' | 表示名 |
| is_active | 有効フラグ | BOOLEAN | - | - | × | True | アカウント有効/無効 |
| is_staff | スタッフフラグ | BOOLEAN | - | - | × | False | Django管理画面アクセス |
| is_superuser | スーパーユーザー | BOOLEAN | - | - | × | False | 全権限 |
| date_joined | 登録日時 | TIMESTAMP | - | - | × | NOW | アカウント作成日時 |
| last_login | 最終ログイン | TIMESTAMP | - | - | ○ | - | 最後にログインした日時 |

**制約**:
- UNIQUE: email
- INDEX: client_code

**備考**:
- AbstractBaseUser を継承
- パスワードは PBKDF2 でハッシュ化

### 2.2 documents_client (取引先)

取引先企業の基本情報を管理します。

| 物理名 | 論理名 | 型 | PK | FK | NULL | デフォルト | 説明 |
|-------|--------|---|----|----|------|-----------|------|
| id | ID | BIGINT | ○ | - | × | AUTO | 主キー |
| client_code | 取引先コード | VARCHAR(5) | - | - | × | - | 5桁の数字（一意） |
| client_name | 取引先名 | VARCHAR(200) | - | - | × | - | 正式名称 |
| postal_code | 郵便番号 | VARCHAR(8) | - | - | × | - | XXX-XXXX |
| address | 住所 | VARCHAR(500) | - | - | × | - | 都道府県から |
| phone_number | 電話番号 | VARCHAR(20) | - | - | × | - | ハイフン含む |
| fax_number | FAX番号 | VARCHAR(20) | - | - | ○ | '' | ハイフン含む |
| email | 代表メールアドレス | VARCHAR(254) | - | - | × | - | 会社代表メール |
| created_at | 作成日時 | TIMESTAMP | - | - | × | NOW | レコード作成日時 |
| updated_at | 更新日時 | TIMESTAMP | - | - | × | NOW | レコード更新日時 |

**制約**:
- UNIQUE: client_code

**備考**:
- client_code は新規登録時に指定

### 2.3 documents_group (グループ)

取引先単位のグループ情報を管理します。

| 物理名 | 論理名 | 型 | PK | FK | NULL | デフォルト | 説明 |
|-------|--------|---|----|----|------|-----------|------|
| id | ID | BIGINT | ○ | - | × | AUTO | 主キー |
| client_code | 取引先コード | VARCHAR(5) | - | - | × | - | 取引先との紐付け |
| group_name | グループ名 | VARCHAR(200) | - | - | × | - | グループ表示名 |
| group_password | グループパスワード | VARCHAR(50) | - | - | × | - | PDF暗号化用 |
| created_at | 作成日時 | TIMESTAMP | - | - | × | NOW | レコード作成日時 |
| updated_at | 更新日時 | TIMESTAMP | - | - | × | NOW | レコード更新日時 |

**制約**:
- UNIQUE: client_code

**備考**:
- group_password は平文で保存（PDF暗号化に使用）
- 取引先1件につき1グループ

### 2.4 documents_groupmember (グループメンバー)

グループに所属する担当者情報を管理します。

| 物理名 | 論理名 | 型 | PK | FK | NULL | デフォルト | 説明 |
|-------|--------|---|----|----|------|-----------|------|
| id | ID | BIGINT | ○ | - | × | AUTO | 主キー |
| group_id | グループID | BIGINT | - | ○ | × | - | FK: documents_group.id |
| member_name | 氏名 | VARCHAR(100) | - | - | × | - | 担当者氏名 |
| email | メールアドレス | VARCHAR(254) | - | - | × | - | 連絡先メール |
| created_at | 作成日時 | TIMESTAMP | - | - | × | NOW | レコード作成日時 |
| updated_at | 更新日時 | TIMESTAMP | - | - | × | NOW | レコード更新日時 |

**制約**:
- FK: group_id → documents_group(id) ON DELETE CASCADE

**備考**:
- 1グループに複数のメンバーが所属可能
- メール通知の送信先

### 2.5 documents_cabinet (キャビネット)

文書管理の最上位階層を表すキャビネットです。

| 物理名 | 論理名 | 型 | PK | FK | NULL | デフォルト | 説明 |
|-------|--------|---|----|----|------|-----------|------|
| id | ID | BIGINT | ○ | - | × | AUTO | 主キー |
| name | キャビネット名 | VARCHAR(200) | - | - | × | - | 表示名 |
| description | 説明 | TEXT | - | - | ○ | '' | 説明文 |
| created_at | 作成日時 | TIMESTAMP | - | - | × | NOW | レコード作成日時 |

**備考**:
- 通常は1件のみ作成
- 全取引先共通

### 2.6 documents_folder (フォルダ)

文書を格納する階層構造を管理します。

| 物理名 | 論理名 | 型 | PK | FK | NULL | デフォルト | 説明 |
|-------|--------|---|----|----|------|-----------|------|
| id | ID | BIGINT | ○ | - | × | AUTO | 主キー |
| cabinet_id | キャビネットID | BIGINT | - | ○ | × | - | FK: documents_cabinet.id |
| parent_id | 親フォルダID | BIGINT | - | ○ | ○ | - | FK: documents_folder.id |
| name | フォルダ名 | VARCHAR(200) | - | - | × | - | 表示名 |
| folder_type | フォルダ種別 | VARCHAR(20) | - | - | × | - | client/year/month |
| client_code | 取引先コード | VARCHAR(5) | - | - | ○ | - | client_codeに紐づく |
| year | 年度 | VARCHAR(4) | - | - | ○ | - | YYYY形式 |
| month | 月 | VARCHAR(2) | - | - | ○ | - | MM形式 |
| created_at | 作成日時 | TIMESTAMP | - | - | × | NOW | レコード作成日時 |

**制約**:
- FK: cabinet_id → documents_cabinet(id) ON DELETE CASCADE
- FK: parent_id → documents_folder(id) ON DELETE CASCADE

**備考**:
- 階層構造: キャビネット → 取引先 → 年度 → 月
- folder_type で階層レベルを判定

**フォルダ階層の例**:
```
キャビネット (Cabinet)
└─ 00001 (client)
   └─ 2024 (year)
      ├─ 01月 (month)
      ├─ 02月 (month)
      └─ 12月 (month)
```

### 2.7 documents_document (文書)

請求書PDFファイルの実データと メタデータを管理します。

| 物理名 | 論理名 | 型 | PK | FK | NULL | デフォルト | 説明 |
|-------|--------|---|----|----|------|-----------|------|
| id | ID | BIGINT | ○ | - | × | AUTO | 主キー |
| folder_id | フォルダID | BIGINT | - | ○ | × | - | FK: documents_folder.id |
| file_name | ファイル名 | VARCHAR(255) | - | - | × | - | 元のファイル名 |
| document_type | 文書種別 | VARCHAR(20) | - | - | × | - | monthly/ad-hoc |
| invoice_number | 請求書番号 | VARCHAR(50) | - | - | × | - | 請求書の識別番号 |
| invoice_date | 請求日 | DATE | - | - | × | - | 請求書の日付 |
| version | 版数 | INTEGER | - | - | × | 1 | 同名ファイルの版数 |
| is_latest | 最新版フラグ | BOOLEAN | - | - | × | True | 最新版かどうか |
| file_data | ファイルデータ | BYTEA | - | - | × | - | PDFバイナリデータ |
| file_size | ファイルサイズ | BIGINT | - | - | × | - | バイト数 |
| encrypt_flag | 暗号化フラグ | BOOLEAN | - | - | × | False | 暗号化済みか |
| uploaded_at | アップロード日時 | TIMESTAMP | - | - | × | NOW | 登録日時 |
| uploaded_by_id | アップロードユーザー | BIGINT | - | ○ | ○ | - | FK: documents_user.id |

**制約**:
- FK: folder_id → documents_folder(id) ON DELETE CASCADE
- FK: uploaded_by_id → documents_user(id) ON DELETE SET NULL
- INDEX: (folder_id, is_latest)
- INDEX: invoice_date

**備考**:
- file_data は最大20MBまで
- 同名ファイルは version で管理
- 最新版のみ is_latest=True

### 2.8 documents_folderpermission (フォルダ権限)

フォルダへのアクセス権限を管理します。

| 物理名 | 論理名 | 型 | PK | FK | NULL | デフォルト | 説明 |
|-------|--------|---|----|----|------|-----------|------|
| id | ID | BIGINT | ○ | - | × | AUTO | 主キー |
| folder_id | フォルダID | BIGINT | - | ○ | × | - | FK: documents_folder.id |
| group_id | グループID | BIGINT | - | ○ | × | - | FK: documents_group.id |
| permission | 権限 | VARCHAR(20) | - | - | × | - | read/write/admin |
| granted_at | 付与日時 | TIMESTAMP | - | - | × | NOW | 権限付与日時 |

**制約**:
- FK: folder_id → documents_folder(id) ON DELETE CASCADE
- FK: group_id → documents_group(id) ON DELETE CASCADE
- UNIQUE: (folder_id, group_id)

**備考**:
- 現在は実装されていない（将来拡張用）

### 2.9 documents_registrationrequest (新規登録依頼)

取引先からの新規登録申請を管理します。

| 物理名 | 論理名 | 型 | PK | FK | NULL | デフォルト | 説明 |
|-------|--------|---|----|----|------|-----------|------|
| id | ID | BIGINT | ○ | - | × | AUTO | 主キー |
| client_code | 取引先コード | VARCHAR(5) | - | - | × | - | 申請する取引先コード |
| client_name | 取引先名 | VARCHAR(200) | - | - | × | - | 正式名称 |
| postal_code | 郵便番号 | VARCHAR(8) | - | - | × | - | XXX-XXXX |
| address | 住所 | VARCHAR(500) | - | - | × | - | 都道府県から |
| phone_number | 電話番号 | VARCHAR(20) | - | - | × | - | ハイフン含む |
| fax_number | FAX番号 | VARCHAR(20) | - | - | ○ | '' | ハイフン含む |
| email | 代表メールアドレス | VARCHAR(254) | - | - | × | - | 会社代表メール |
| group_password | グループパスワード | VARCHAR(50) | - | - | × | - | PDF暗号化用 |
| status | ステータス | VARCHAR(20) | - | - | × | pending | pending/approved/rejected |
| requested_at | 申請日時 | TIMESTAMP | - | - | × | NOW | 申請日時 |
| processed_at | 処理日時 | TIMESTAMP | - | - | ○ | - | 承認/却下日時 |
| processed_by_id | 処理者 | BIGINT | - | ○ | ○ | - | FK: documents_user.id |
| reject_reason | 却下理由 | TEXT | - | - | ○ | '' | 却下時の理由 |

**制約**:
- FK: processed_by_id → documents_user(id) ON DELETE SET NULL

**ステータス**:
- pending: 未承認
- approved: 承認済み
- rejected: 却下

### 2.10 documents_registrationrequestcontact (登録依頼担当者)

新規登録申請時の担当者情報を管理します。

| 物理名 | 論理名 | 型 | PK | FK | NULL | デフォルト | 説明 |
|-------|--------|---|----|----|------|-----------|------|
| id | ID | BIGINT | ○ | - | × | AUTO | 主キー |
| request_id | 登録依頼ID | BIGINT | - | ○ | × | - | FK: documents_registrationrequest.id |
| contact_name | 氏名 | VARCHAR(100) | - | - | × | - | 担当者氏名 |
| email | メールアドレス | VARCHAR(254) | - | - | × | - | ログインID |
| password | パスワード | VARCHAR(128) | - | - | × | - | 平文（承認時にハッシュ化） |

**制約**:
- FK: request_id → documents_registrationrequest(id) ON DELETE CASCADE

**備考**:
- 承認時に User と GroupMember を作成
- password は申請時は平文、承認時にハッシュ化

### 2.11 documents_changerequest (変更依頼)

プロフィール・担当者の変更申請を管理します。

| 物理名 | 論理名 | 型 | PK | FK | NULL | デフォルト | 説明 |
|-------|--------|---|----|----|------|-----------|------|
| id | ID | BIGINT | ○ | - | × | AUTO | 主キー |
| client_id | 取引先ID | BIGINT | - | ○ | × | - | FK: documents_client.id |
| change_type | 変更種別 | VARCHAR(20) | - | - | × | - | profile/member_add/member_delete |
| client_name | 取引先名 | VARCHAR(200) | - | - | ○ | - | 変更後の取引先名 |
| postal_code | 郵便番号 | VARCHAR(8) | - | - | ○ | - | 変更後の郵便番号 |
| address | 住所 | VARCHAR(500) | - | - | ○ | - | 変更後の住所 |
| phone_number | 電話番号 | VARCHAR(20) | - | - | ○ | - | 変更後の電話番号 |
| fax_number | FAX番号 | VARCHAR(20) | - | - | ○ | '' | 変更後のFAX番号 |
| email | 代表メールアドレス | VARCHAR(254) | - | - | ○ | - | 変更後のメール |
| status | ステータス | VARCHAR(20) | - | - | × | pending | pending/approved/rejected |
| requested_at | 申請日時 | TIMESTAMP | - | - | × | NOW | 申請日時 |
| requested_by_id | 申請者 | BIGINT | - | ○ | ○ | - | FK: documents_user.id |
| processed_at | 処理日時 | TIMESTAMP | - | - | ○ | - | 承認/却下日時 |
| processed_by_id | 処理者 | BIGINT | - | ○ | ○ | - | FK: documents_user.id |
| reject_reason | 却下理由 | TEXT | - | - | ○ | '' | 却下時の理由 |

**制約**:
- FK: client_id → documents_client(id) ON DELETE CASCADE
- FK: requested_by_id → documents_user(id) ON DELETE SET NULL
- FK: processed_by_id → documents_user(id) ON DELETE SET NULL

**変更種別**:
- profile: プロフィール変更
- member_add: 担当者追加
- member_delete: 担当者削除

### 2.12 documents_changerequestcontact (変更依頼担当者)

変更申請時の担当者情報を管理します。

| 物理名 | 論理名 | 型 | PK | FK | NULL | デフォルト | 説明 |
|-------|--------|---|----|----|------|-----------|------|
| id | ID | BIGINT | ○ | - | × | AUTO | 主キー |
| request_id | 変更依頼ID | BIGINT | - | ○ | × | - | FK: documents_changerequest.id |
| action | アクション | VARCHAR(20) | - | - | × | - | add/update/delete |
| member_id | メンバーID | BIGINT | - | ○ | ○ | - | FK: documents_groupmember.id |
| contact_name | 氏名 | VARCHAR(100) | - | - | ○ | - | 担当者氏名 |
| email | メールアドレス | VARCHAR(254) | - | - | ○ | - | ログインID |
| password | パスワード | VARCHAR(128) | - | - | ○ | - | 追加時のみ |

**制約**:
- FK: request_id → documents_changerequest(id) ON DELETE CASCADE
- FK: member_id → documents_groupmember(id) ON DELETE SET NULL

**アクション**:
- add: 担当者追加
- update: 担当者情報変更
- delete: 担当者削除

---

## 3. ER図

### 3.1 エンティティ関連図

```
┌─────────────────┐
│  User           │
│  (利用者)       │
└────┬────────────┘
     │1
     │
     │*
┌────┴────────────┐         ┌─────────────────┐
│  Client         │1      1 │  Group          │
│  (取引先)       ├─────────┤  (グループ)     │
└─────────────────┘         └────┬────────────┘
                                 │1
                                 │
                                 │*
                            ┌────┴────────────┐
                            │ GroupMember     │
                            │ (グループメンバー)│
                            └─────────────────┘

┌─────────────────┐
│  Cabinet        │
│  (キャビネット) │
└────┬────────────┘
     │1
     │
     │*
┌────┴────────────┐
│  Folder         │
│  (フォルダ)     │◄──┐
└────┬────────────┘   │ 自己参照
     │1               │ (parent)
     │                │
     │*               │
┌────┴────────────┐   │
│  Document       │   │
│  (文書)         │   │
└─────────────────┘   │
                      │
┌─────────────────┐   │
│ FolderPermission│   │
│ (フォルダ権限)  ├───┘
└─────────────────┘

┌──────────────────────┐
│ RegistrationRequest  │
│ (新規登録依頼)       │
└────┬─────────────────┘
     │1
     │
     │*
┌────┴─────────────────────────┐
│ RegistrationRequestContact   │
│ (登録依頼担当者)             │
└──────────────────────────────┘

┌─────────────────┐
│ ChangeRequest   │
│ (変更依頼)      │
└────┬────────────┘
     │1
     │
     │*
┌────┴────────────────────┐
│ ChangeRequestContact    │
│ (変更依頼担当者)        │
└─────────────────────────┘
```

### 3.2 リレーションシップ

| 親テーブル | 子テーブル | 関係 | 説明 |
|----------|----------|------|------|
| Cabinet | Folder | 1:N | 1キャビネットに複数フォルダ |
| Folder | Folder | 1:N | 階層構造（自己参照） |
| Folder | Document | 1:N | 1フォルダに複数文書 |
| Group | GroupMember | 1:N | 1グループに複数メンバー |
| User | Document | 1:N | 1ユーザーが複数文書をアップロード |
| RegistrationRequest | RegistrationRequestContact | 1:N | 1依頼に複数担当者 |
| ChangeRequest | ChangeRequestContact | 1:N | 1依頼に複数担当者 |

---

## 4. インデックス設計

### 4.1 主キーインデックス

すべてのテーブルで `id` カラムに主キーインデックスが自動作成されます。

### 4.2 一意制約インデックス

| テーブル | カラム | 目的 |
|---------|--------|------|
| User | email | メールアドレスの一意性保証 |
| Client | client_code | 取引先コードの一意性保証 |
| Group | client_code | 取引先とグループの1:1保証 |

### 4.3 外部キーインデックス

Django が自動的に作成する外部キーインデックス:
- folder.cabinet_id
- folder.parent_id
- document.folder_id
- document.uploaded_by_id
- groupmember.group_id
- 等

### 4.4 検索用インデックス

| テーブル | カラム | 目的 |
|---------|--------|------|
| User | client_code | 取引先コードでのユーザー検索 |
| Document | (folder_id, is_latest) | 最新文書の高速検索 |
| Document | invoice_date | 請求日での検索 |

**作成SQL例**:
```sql
CREATE INDEX idx_user_client_code ON documents_user(client_code);
CREATE INDEX idx_document_folder_latest ON documents_document(folder_id, is_latest);
CREATE INDEX idx_document_invoice_date ON documents_document(invoice_date);
```

---

## 5. 制約定義

### 5.1 NOT NULL制約

| テーブル | カラム | 理由 |
|---------|--------|------|
| User | email, user_type | 必須項目 |
| Client | client_code, client_name | 必須項目 |
| Document | file_name, file_data | 必須項目 |
| 全テーブル | created_at | 作成日時は必須 |

### 5.2 UNIQUE制約

| テーブル | カラム | 理由 |
|---------|--------|------|
| User | email | ログインIDの一意性 |
| Client | client_code | 取引先コードの一意性 |
| Group | client_code | 1取引先1グループ |
| FolderPermission | (folder_id, group_id) | 重複権限防止 |

### 5.3 外部キー制約

| 子テーブル | 子カラム | 親テーブル | 親カラム | ON DELETE |
|----------|---------|----------|---------|-----------|
| Folder | cabinet_id | Cabinet | id | CASCADE |
| Folder | parent_id | Folder | id | CASCADE |
| Document | folder_id | Folder | id | CASCADE |
| Document | uploaded_by_id | User | id | SET NULL |
| GroupMember | group_id | Group | id | CASCADE |
| FolderPermission | folder_id | Folder | id | CASCADE |
| FolderPermission | group_id | Group | id | CASCADE |
| RegistrationRequestContact | request_id | RegistrationRequest | id | CASCADE |
| ChangeRequest | client_id | Client | id | CASCADE |
| ChangeRequestContact | request_id | ChangeRequest | id | CASCADE |

**ON DELETE の意味**:
- CASCADE: 親を削除すると子も削除
- SET NULL: 親を削除すると子のFKをNULLに設定

### 5.4 CHECK制約

Django モデルレベルで実装:

**User.user_type**:
```python
user_type = models.CharField(
    choices=[('admin', '管理者'), ('staff', 'スタッフ'), 
             ('client', '取引先'), ('api', 'API')]
)
```

**Document.document_type**:
```python
document_type = models.CharField(
    choices=[('monthly', '月次請求書'), ('ad-hoc', '随時請求書')]
)
```

**RegistrationRequest.status**:
```python
status = models.CharField(
    choices=[('pending', '未承認'), ('approved', '承認済'), ('rejected', '却下')]
)
```

### 5.5 デフォルト値制約

| テーブル | カラム | デフォルト値 |
|---------|--------|------------|
| User | is_active | True |
| User | is_staff | False |
| User | is_superuser | False |
| Document | version | 1 |
| Document | is_latest | True |
| Document | encrypt_flag | False |
| RegistrationRequest | status | 'pending' |
| ChangeRequest | status | 'pending' |

---

## 付録

### A. データサイズ見積もり

**前提条件**:
- 取引先数: 100社
- 担当者数: 1社あたり平均3名 = 300名
- 文書数: 1社あたり月1件 × 12ヶ月 = 年間1,200件
- PDFサイズ: 平均1MB

**年間データ量**:
```
文書データ: 1,200件 × 1MB = 1.2GB/年
メタデータ: 約10MB（無視できる）
合計: 約1.2GB/年
```

**5年間の見積もり**: 約6GB

### B. バックアップ戦略

**フルバックアップ**:
- 頻度: 週次（日曜深夜）
- 保持期間: 4週間

**差分バックアップ**:
- 頻度: 日次（毎日深夜）
- 保持期間: 7日間

**バックアップ容量**:
- 初年度: 約1.2GB
- 5年後: 約6GB

### C. データ削除ポリシー

**論理削除**:
- User.is_active = False

**物理削除**:
- 承認・却下後1年経過した申請データ
- 削除依頼された文書（管理者のみ）

---

**文書終わり**
