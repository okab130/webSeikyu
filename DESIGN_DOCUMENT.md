# WEB請求書システム 詳細設計書

**バージョン**: 1.0  
**作成日**: 2024-12-21  
**最終更新日**: 2024-12-21

---

## 目次

1. [機能概要](#1-機能概要)
2. [機能一覧](#2-機能一覧)
3. [機能詳細](#3-機能詳細)
4. [画面詳細](#4-画面詳細)
5. [API仕様](#5-api仕様)
6. [非機能設計](#6-非機能設計)

---

## 1. 機能概要

### 1.1 システム概要

WEB請求書システムは、請求書PDFファイルをオンラインで管理・配信するためのWebアプリケーションです。取引先は請求書をWeb経由でダウンロードでき、管理者は請求書の登録・管理を行えます。

### 1.2 システムの目的

- 請求書の電子配信によるペーパーレス化
- 配送コスト・時間の削減
- 請求書の確実な配信と履歴管理
- セキュアな文書管理（PDF暗号化）

### 1.3 システム構成

```
┌─────────────────────────────────────────────────────────┐
│                    Webブラウザ                           │
│          (Chrome, Firefox, Safari, Edge)                │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTPS
                   ↓
┌─────────────────────────────────────────────────────────┐
│                  Webサーバー                             │
│              Django 6.0 (Python 3.13)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  View Layer                                       │  │
│  │  - Staff Views (管理者画面)                      │  │
│  │  - Client Views (取引先画面)                     │  │
│  │  - API Views (API連携)                           │  │
│  └──────────────────┬───────────────────────────────┘  │
│                     ↓                                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Model Layer                                      │  │
│  │  - User, Client, Group                           │  │
│  │  - Document, Folder, Cabinet                     │  │
│  │  - RegistrationRequest, ChangeRequest            │  │
│  └──────────────────┬───────────────────────────────┘  │
└────────────────────┼───────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              PostgreSQL Database                        │
│          (文書データはバイナリで保存)                    │
└─────────────────────────────────────────────────────────┘
```

### 1.4 ユーザー種別

| ユーザー種別 | 説明 | 主な機能 |
|------------|------|---------|
| **admin** | システム管理者 | Django管理画面での全データ管理 |
| **staff** | 事務担当者 | 承認業務、文書管理、取引先管理 |
| **client** | 取引先担当者 | 文書閲覧・ダウンロード、プロフィール管理 |
| **api** | APIユーザー | API経由での文書登録のみ |

### 1.5 技術スタック

| 項目 | 技術 | バージョン |
|-----|------|----------|
| プログラミング言語 | Python | 3.13 |
| Webフレームワーク | Django | 6.0 |
| データベース | PostgreSQL | 最新版 |
| フロントエンド | Bootstrap | 5.x |
| PDF処理 | PyPDF2 | 3.0.1 |
| 画像処理 | Pillow | 12.0.0 |

---

## 2. 機能一覧

### 2.1 共通機能

| 機能ID | 機能名 | 説明 | ユーザー種別 |
|-------|--------|------|------------|
| COM-001 | ログイン | メールアドレスとパスワードでログイン | 全ユーザー |
| COM-002 | ログアウト | システムからログアウト | 全ユーザー |
| COM-003 | パスワード変更 | ログインパスワードの変更 | staff, client |
| COM-004 | 操作マニュアル閲覧 | HTML形式のマニュアル表示 | staff, client |

### 2.2 取引先機能

| 機能ID | 機能名 | 説明 | 画面 |
|-------|--------|------|------|
| CLI-001 | 新規登録申請 | 取引先の新規登録依頼 | 新規登録画面 |
| CLI-002 | ダッシュボード | 最新文書の表示 | ダッシュボード |
| CLI-003 | 文書一覧 | 請求書一覧の表示・検索 | 文書一覧 |
| CLI-004 | 文書詳細 | 請求書の詳細情報表示 | 文書詳細 |
| CLI-005 | 文書ダウンロード | PDFファイルのダウンロード | - |
| CLI-006 | プロフィール閲覧 | 取引先情報・担当者一覧表示 | プロフィール |
| CLI-007 | プロフィール編集申請 | 取引先情報の変更申請 | プロフィール編集 |
| CLI-008 | 担当者追加申請 | 新しい担当者の追加申請 | プロフィール編集 |
| CLI-009 | 担当者削除申請 | 既存担当者の削除申請 | プロフィール編集 |
| CLI-010 | 操作マニュアル | 取引先向けマニュアル表示 | マニュアル |

### 2.3 スタッフ機能

| 機能ID | 機能名 | 説明 | 画面 |
|-------|--------|------|------|
| STF-001 | ダッシュボード | 未承認依頼の一覧表示 | ダッシュボード |
| STF-002 | 新規登録依頼一覧 | 登録依頼の一覧表示 | 登録依頼一覧 |
| STF-003 | 新規登録依頼詳細 | 登録依頼の詳細表示 | 登録依頼詳細 |
| STF-004 | 新規登録承認 | 登録依頼の承認処理 | 登録依頼詳細 |
| STF-005 | 新規登録却下 | 登録依頼の却下処理 | 登録依頼詳細 |
| STF-006 | 変更依頼一覧 | 変更依頼の一覧表示 | 変更依頼一覧 |
| STF-007 | 変更依頼詳細 | 変更依頼の詳細表示 | 変更依頼詳細 |
| STF-008 | 変更依頼承認 | 変更依頼の承認処理 | 変更依頼詳細 |
| STF-009 | 変更依頼却下 | 変更依頼の却下処理 | 変更依頼詳細 |
| STF-010 | 取引先一覧 | 取引先の一覧表示 | 取引先一覧 |
| STF-011 | 取引先詳細 | 取引先情報の詳細表示 | 取引先詳細 |
| STF-012 | 文書検索 | 文書の検索 | 文書検索 |
| STF-013 | 文書詳細 | 文書の詳細表示 | 文書詳細 |
| STF-014 | 文書アップロード | PDFファイルの登録 | 文書アップロード |
| STF-015 | 文書削除 | 文書の削除 | 文書詳細 |
| STF-016 | 文書ダウンロード | PDFファイルのダウンロード | - |
| STF-017 | 操作マニュアル | 管理者向けマニュアル表示 | マニュアル |

### 2.4 API機能

| 機能ID | 機能名 | 説明 | エンドポイント |
|-------|--------|------|---------------|
| API-001 | APIログイン | セッション認証 | POST /api/login/ |
| API-002 | APIログアウト | セッション破棄 | POST /api/logout/ |
| API-003 | 文書アップロード | PDF文書の登録 | POST /api/documents/upload/ |

### 2.5 管理機能

| 機能ID | 機能名 | 説明 | 画面 |
|-------|--------|------|------|
| ADM-001 | ユーザー管理 | ユーザーの追加・編集・削除 | Django Admin |
| ADM-002 | 取引先管理 | 取引先マスタの管理 | Django Admin |
| ADM-003 | グループ管理 | グループの管理 | Django Admin |
| ADM-004 | 文書管理 | 文書の直接編集・削除 | Django Admin |
| ADM-005 | フォルダ管理 | フォルダ構造の管理 | Django Admin |

---

## 3. 機能詳細

### 3.1 共通機能

#### 3.1.1 ログイン (COM-001)

**目的**: ユーザー認証とセッション確立

**処理フロー**:
```
1. ユーザーがメールアドレスとパスワードを入力
2. システムがユーザー情報を検証
3. 認証成功時、セッションを作成
4. ユーザー種別に応じたダッシュボードにリダイレクト
   - staff → スタッフダッシュボード
   - client → 取引先ダッシュボード
   - api → API専用（画面ログイン不可）
```

**バリデーション**:
- メールアドレス: 必須、形式チェック
- パスワード: 必須
- is_active: True

**エラーハンドリング**:
- 認証失敗: "メールアドレスまたはパスワードが正しくありません"
- アカウント無効: "このアカウントは無効化されています"

#### 3.1.2 ログアウト (COM-002)

**目的**: セッションの破棄

**処理フロー**:
```
1. ユーザーがログアウトボタンをクリック
2. セッションを破棄
3. ログイン画面にリダイレクト
```

### 3.2 取引先機能

#### 3.2.1 新規登録申請 (CLI-001)

**目的**: 新規取引先の登録依頼

**入力項目**:

| 項目 | 型 | 必須 | 説明 |
|-----|---|------|------|
| 取引先コード | CHAR(5) | ○ | 5桁の数字 |
| 取引先名 | VARCHAR(200) | ○ | 正式名称 |
| 郵便番号 | CHAR(8) | ○ | XXX-XXXX形式 |
| 住所 | VARCHAR(500) | ○ | 都道府県から |
| 電話番号 | VARCHAR(20) | ○ | ハイフン含む |
| FAX番号 | VARCHAR(20) | - | ハイフン含む |
| 代表メールアドレス | EMAIL | ○ | 会社代表メール |
| グループパスワード | VARCHAR(50) | ○ | PDF暗号化用 |
| 担当者氏名 | VARCHAR(100) | ○ | 代表者氏名 |
| 担当者メール | EMAIL | ○ | ログインID |
| 担当者パスワード | VARCHAR | ○ | 8文字以上 |

**処理フロー**:
```
1. 入力フォーム表示
2. バリデーション実行
3. RegistrationRequest作成
4. RegistrationRequestContact作成
5. 確認画面表示
6. 管理者にメール通知（オプション）
```

**バリデーション**:
- 取引先コード: 5桁の数字、重複チェック
- メールアドレス: 形式チェック、重複チェック
- パスワード: 8文字以上、英数字含む

#### 3.2.2 文書ダウンロード (CLI-005)

**目的**: 請求書PDFのダウンロード

**処理フロー**:
```
1. ユーザーがダウンロードボタンをクリック
2. 権限チェック（自社の文書のみ）
3. file_dataからバイナリデータを取得
4. Content-Dispositionヘッダーを設定
5. PDFファイルを返却
6. 暗号化されている場合、グループパスワードが必要
```

**セキュリティ**:
- 自社の取引先コードの文書のみアクセス可能
- 最新版のみダウンロード可能（is_latest=True）

### 3.3 スタッフ機能

#### 3.3.1 新規登録承認 (STF-004)

**目的**: 登録依頼の承認と取引先データの作成

**処理フロー**:
```
@transaction.atomic
1. RegistrationRequestのステータス確認（pending）
2. Client作成
3. Group作成
4. GroupMember作成
5. User作成（user_type='client'）
6. RegistrationRequestのステータス更新（approved）
7. 承認日時・承認者を記録
8. 申請者にメール通知
```

**ロールバック条件**:
- 取引先コード重複
- メールアドレス重複
- その他DB制約違反

#### 3.3.2 文書アップロード (STF-014)

**目的**: 請求書PDFの登録

**入力項目**:

| 項目 | 型 | 必須 | 説明 |
|-----|---|------|------|
| 取引先コード | CHAR(5) | ○ | 登録済みコード |
| 文書種別 | VARCHAR(20) | ○ | monthly/ad-hoc |
| 請求書番号 | VARCHAR(50) | ○ | 一意の番号 |
| 請求日 | DATE | ○ | 請求書の日付 |
| PDFファイル | FILE | ○ | 最大20MB |
| 暗号化フラグ | BOOLEAN | - | デフォルトFalse |

**処理フロー**:
```
@transaction.atomic
1. 入力バリデーション
2. 取引先存在チェック
3. フォルダ自動作成
   - 取引先フォルダ（client_code）
   - 年度フォルダ（YYYY）
   - 月フォルダ（MM月）
4. 同名ファイルチェック
   - 存在する場合: version++, is_latest更新
   - 新規の場合: version=1
5. 暗号化処理（encrypt_flag=Trueの場合）
   - グループパスワード取得
   - PyPDF2で暗号化
6. Documentレコード作成
7. メール通知（取引先全担当者）
```

**自動処理**:
- フォルダ構造の自動作成
- 版数管理
- PDF暗号化
- メール通知

### 3.4 API機能

#### 3.4.1 文書アップロード API (API-003)

**エンドポイント**: `POST /api/documents/upload/`

**認証**: セッション認証（事前にログイン必要）

**リクエスト形式**: `multipart/form-data`

**パラメータ**:

| パラメータ名 | 型 | 必須 | 説明 |
|------------|---|------|------|
| client_code | string | ○ | 取引先コード（5桁） |
| document_type | string | ○ | monthly or ad-hoc |
| invoice_number | string | ○ | 請求書番号 |
| invoice_date | string | ○ | YYYY-MM-DD形式 |
| file | file | ○ | PDFファイル |
| encrypt_flag | boolean | - | true or false |

**レスポンス例**:

成功時:
```json
{
  "status": "success",
  "message": "文書を登録しました",
  "document_id": 123,
  "version": 2
}
```

エラー時:
```json
{
  "status": "error",
  "message": "取引先コードが見つかりません"
}
```

---

## 4. 画面詳細

### 4.1 画面一覧

#### 4.1.1 共通画面

| 画面ID | 画面名 | URL | テンプレート |
|-------|--------|-----|-------------|
| CMN-001 | ログイン画面 | /login/ | login.html |
| CMN-002 | 新規登録画面 | /register/ | register.html |
| CMN-003 | 登録確認画面 | /register/confirm/ | register_confirm.html |

#### 4.1.2 取引先画面

| 画面ID | 画面名 | URL | テンプレート |
|-------|--------|-----|-------------|
| CLI-001 | ダッシュボード | /client/dashboard/ | client/dashboard.html |
| CLI-002 | 文書一覧 | /client/documents/ | client/document_list.html |
| CLI-003 | プロフィール | /client/profile/ | client/profile.html |
| CLI-004 | プロフィール編集 | /client/profile/edit/ | client/profile_edit.html |
| CLI-005 | 操作マニュアル | /client/manual/ | client/manual.html |

#### 4.1.3 スタッフ画面

| 画面ID | 画面名 | URL | テンプレート |
|-------|--------|-----|-------------|
| STF-001 | ダッシュボード | /staff/dashboard/ | staff/dashboard.html |
| STF-002 | 登録依頼一覧 | /staff/registration-requests/ | staff/registration_list.html |
| STF-003 | 登録依頼詳細 | /staff/registration-requests/{id}/ | staff/registration_detail.html |
| STF-004 | 変更依頼一覧 | /staff/change-requests/ | staff/change_list.html |
| STF-005 | 変更依頼詳細 | /staff/change-requests/{id}/ | staff/change_detail.html |
| STF-006 | 取引先一覧 | /staff/clients/ | staff/client_list.html |
| STF-007 | 取引先詳細 | /staff/clients/{id}/ | staff/client_detail.html |
| STF-008 | 文書検索 | /staff/documents/search/ | staff/document_search.html |
| STF-009 | 文書詳細 | /staff/documents/{id}/ | staff/document_detail.html |
| STF-010 | 文書アップロード | /staff/documents/upload/ | staff/document_upload.html |
| STF-011 | 操作マニュアル | /staff/manual/ | staff/manual.html |

### 4.2 画面レイアウト

#### 4.2.1 共通レイアウト (base.html)

**構成要素**:
```
┌─────────────────────────────────────────┐
│ ヘッダー                                 │
│ - ロゴ                                   │
│ - ナビゲーションメニュー                 │
│ - ユーザー情報・ログアウト               │
├─────────────────────────────────────────┤
│                                         │
│ コンテンツエリア                         │
│ （各画面固有のコンテンツ）               │
│                                         │
├─────────────────────────────────────────┤
│ フッター                                 │
│ - コピーライト                           │
│ - バージョン情報                         │
└─────────────────────────────────────────┘
```

**使用技術**:
- Bootstrap 5.x
- Bootstrap Icons
- レスポンシブデザイン

#### 4.2.2 ダッシュボード画面詳細

**スタッフダッシュボード** (STF-001):

```
┌─────────────────────────────────────────┐
│ スタッフダッシュボード                   │
├─────────────────────────────────────────┤
│ ┌───────────────┐ ┌───────────────┐   │
│ │新規登録依頼   │ │変更依頼       │   │
│ │（未承認）     │ │（未承認）     │   │
│ │- 依頼1        │ │- 依頼1        │   │
│ │- 依頼2        │ │- 依頼2        │   │
│ └───────────────┘ └───────────────┘   │
├─────────────────────────────────────────┤
│ クイックアクション                       │
│ [取引先一覧] [文書検索]                  │
│ [文書アップロード] [管理画面]            │
│ [操作マニュアル]                         │
└─────────────────────────────────────────┘
```

**取引先ダッシュボード** (CLI-001):

```
┌─────────────────────────────────────────┐
│ ダッシュボード                           │
├─────────────────────────────────────────┤
│ クイックアクション                       │
│ [文書一覧] [プロフィール]                │
│ [操作マニュアル]                         │
├─────────────────────────────────────────┤
│ 請求書フォルダ                           │
│ 📁 2024                                 │
│   📁 12月                               │
│     📄 invoice_202412_001.pdf          │
│     📄 invoice_202412_002.pdf          │
│   📁 11月                               │
│     📄 invoice_202411_001.pdf          │
└─────────────────────────────────────────┘
```

### 4.3 画面遷移図

```
[ログイン] 
    ├─ [スタッフ] → [スタッフダッシュボード]
    │                  ├─ [登録依頼一覧] → [登録依頼詳細]
    │                  ├─ [変更依頼一覧] → [変更依頼詳細]
    │                  ├─ [取引先一覧] → [取引先詳細]
    │                  ├─ [文書検索] → [文書詳細]
    │                  ├─ [文書アップロード]
    │                  └─ [操作マニュアル]
    │
    └─ [取引先] → [取引先ダッシュボード]
                      ├─ [文書一覧]
                      ├─ [プロフィール] → [プロフィール編集]
                      └─ [操作マニュアル]

[新規登録] → [登録確認]
```

---

## 5. API仕様

### 5.1 認証

**方式**: セッション認証（Django標準）

**フロー**:
```
1. POST /api/login/
   → セッションID発行
2. 以降のリクエストでセッションIDを使用
3. POST /api/logout/
   → セッション破棄
```

### 5.2 APIエンドポイント一覧

| エンドポイント | メソッド | 認証 | 説明 |
|--------------|---------|------|------|
| /api/login/ | POST | 不要 | ログイン |
| /api/logout/ | POST | 必要 | ログアウト |
| /api/documents/upload/ | POST | 必要 | 文書アップロード |

### 5.3 API詳細仕様

#### 5.3.1 ログイン API

**エンドポイント**: `POST /api/login/`

**リクエスト**:
```json
{
  "email": "api@example.com",
  "password": "password123"
}
```

**レスポンス**:

成功時 (200):
```json
{
  "status": "success",
  "message": "ログインしました",
  "user": {
    "email": "api@example.com",
    "user_type": "api"
  }
}
```

エラー時 (401):
```json
{
  "status": "error",
  "message": "メールアドレスまたはパスワードが正しくありません"
}
```

#### 5.3.2 文書アップロード API

**エンドポイント**: `POST /api/documents/upload/`

**リクエストヘッダー**:
```
Content-Type: multipart/form-data
Cookie: sessionid=xxxxx
```

**リクエストボディ**:

| フィールド | 型 | 必須 | 説明 |
|----------|---|------|------|
| client_code | string | ○ | 取引先コード |
| document_type | string | ○ | monthly/ad-hoc |
| invoice_number | string | ○ | 請求書番号 |
| invoice_date | string | ○ | YYYY-MM-DD |
| file | file | ○ | PDFファイル |
| encrypt_flag | string | - | true/false |

**レスポンス**:

成功時 (200):
```json
{
  "status": "success",
  "message": "文書を登録しました",
  "document_id": 123,
  "version": 1
}
```

エラー時 (400):
```json
{
  "status": "error",
  "message": "取引先コードが見つかりません"
}
```

エラー時 (401):
```json
{
  "status": "error",
  "message": "認証されていません"
}
```

エラー時 (500):
```json
{
  "status": "error",
  "message": "PDF暗号化エラー: xxxxx"
}
```

### 5.4 curlサンプル

#### Windowsの場合

**ログイン**:
```powershell
$headers = @{
    "Content-Type" = "application/json"
}
$body = @{
    email = "api@example.com"
    password = "password123"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/login/" `
    -Method POST `
    -Headers $headers `
    -Body $body `
    -SessionVariable session
```

**文書アップロード**:
```powershell
$form = @{
    client_code = "00001"
    document_type = "monthly"
    invoice_number = "INV-00001-202412-001"
    invoice_date = "2024-12-21"
    encrypt_flag = "true"
    file = Get-Item -Path "C:\path\to\invoice.pdf"
}

Invoke-WebRequest -Uri "http://localhost:8000/api/documents/upload/" `
    -Method POST `
    -Form $form `
    -WebSession $session
```

#### Linuxの場合

**ログイン**:
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"api@example.com","password":"password123"}' \
  -c cookies.txt
```

**文書アップロード**:
```bash
curl -X POST http://localhost:8000/api/documents/upload/ \
  -F "client_code=00001" \
  -F "document_type=monthly" \
  -F "invoice_number=INV-00001-202412-001" \
  -F "invoice_date=2024-12-21" \
  -F "encrypt_flag=true" \
  -F "file=@/path/to/invoice.pdf" \
  -b cookies.txt
```

---

## 6. 非機能設計

### 6.1 セキュリティ設計

#### 6.1.1 認証・認可

**認証方式**:
- セッション認証（Django標準）
- パスワードハッシュ化（PBKDF2）

**認可制御**:
- Mixin による権限チェック
  - `StaffRequiredMixin`: staff のみアクセス可
  - `ClientRequiredMixin`: client のみアクセス可
- 取引先データは自社のみアクセス可能

**セッション管理**:
```python
# settings.py
SESSION_COOKIE_AGE = 3600  # 1時間
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True  # HTTPS環境
```

#### 6.1.2 PDF暗号化

**暗号化方式**: 128bit AES (PyPDF2)

**パスワード管理**:
- グループパスワードをDB保存（平文）
- アップロード時にPDFを暗号化
- ダウンロード時は暗号化済みPDFを返却

**暗号化フロー**:
```python
if encrypt_flag:
    group = Group.objects.get(client_code=client_code)
    encrypted_data = encrypt_pdf(file_data, group.group_password)
```

#### 6.1.3 CSRF対策

**実装**:
- Django標準のCSRF保護を有効化
- すべてのフォームに `{% csrf_token %}`
- API は `@csrf_exempt` で除外

#### 6.1.4 SQLインジェクション対策

**実装**:
- Django ORM使用（プリペアドステートメント）
- 生SQLは使用しない

#### 6.1.5 XSS対策

**実装**:
- テンプレートの自動エスケープ
- `|safe` フィルターは使用しない

### 6.2 パフォーマンス設計

#### 6.2.1 データベース最適化

**インデックス**:
```python
# models.py
class User(AbstractBaseUser):
    client_code = models.CharField(db_index=True)  # インデックス

class Document(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['folder', 'is_latest']),
            models.Index(fields=['invoice_date']),
        ]
```

**N+1問題対策**:
```python
# select_related (ForeignKey)
documents = Document.objects.select_related('folder', 'uploaded_by')

# prefetch_related (ManyToMany, reverse FK)
groups = Group.objects.prefetch_related('members')
```

#### 6.2.2 ファイルサイズ制限

**制限値**:
- PDFファイル: 最大20MB
- バリデーション: フォームレベルで実施

```python
# forms.py
def clean_file(self):
    file = self.cleaned_data.get('file')
    if file.size > 20 * 1024 * 1024:  # 20MB
        raise ValidationError('ファイルサイズは20MB以下にしてください')
    return file
```

#### 6.2.3 クエリ最適化

**全件検索の制限**:
- ページネーション実装
- 1ページあたり最大100件

```python
# views.py
class DocumentListView(ListView):
    paginate_by = 50
```

### 6.3 可用性設計

#### 6.3.1 エラーハンドリング

**トランザクション管理**:
```python
from django.db import transaction

@transaction.atomic
def approve_registration(request_id):
    # すべて成功 or すべてロールバック
    pass
```

**例外処理**:
```python
try:
    document = Document.objects.get(id=document_id)
except Document.DoesNotExist:
    raise Http404('文書が見つかりません')
```

#### 6.3.2 ログ設計

**ログレベル**:
- DEBUG: 開発環境のみ
- INFO: 通常の操作ログ
- WARNING: 警告
- ERROR: エラー
- CRITICAL: システムダウン級

**ログ出力先**:
```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/webseikyu/app.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

### 6.4 保守性設計

#### 6.4.1 コーディング規約

**準拠規格**:
- PEP 8 (Python標準)
- Django Coding Style

**命名規則**:
- クラス: PascalCase
- 関数・変数: snake_case
- 定数: UPPER_CASE

#### 6.4.2 テスト設計

**テスト種別**:
- 単体テスト: Django TestCase
- 統合テスト: TransactionTestCase
- E2Eテスト: Selenium (将来実装)

**カバレッジ目標**: 80%以上

#### 6.4.3 バージョン管理

**ブランチ戦略**:
- main: 本番環境
- develop: 開発環境
- feature/*: 機能開発

**コミットメッセージ**:
```
feat: 新機能追加
fix: バグ修正
docs: ドキュメント更新
test: テスト追加
refactor: リファクタリング
```

### 6.5 運用設計

#### 6.5.1 バックアップ

**対象**:
- PostgreSQLデータベース
- 設定ファイル

**頻度**:
- 日次: 増分バックアップ
- 週次: 完全バックアップ

**保持期間**: 90日

#### 6.5.2 監視

**監視項目**:
- サーバーリソース (CPU, メモリ, ディスク)
- レスポンスタイム
- エラーログ
- ディスク容量

**アラート条件**:
- レスポンスタイム > 5秒
- エラー率 > 5%
- ディスク使用率 > 90%

#### 6.5.3 デプロイ

**デプロイ方式**:
1. Git pull
2. マイグレーション実行
3. 静的ファイル収集
4. Webサーバー再起動

**ダウンタイム**: 最小化（Blue-Green デプロイ推奨）

### 6.6 スケーラビリティ設計

#### 6.6.1 水平スケーリング

**対応方法**:
- Webサーバー: 複数台構成可能
- ロードバランサー: Nginx推奨
- セッション: Redis等の外部ストア使用

#### 6.6.2 ストレージ

**現状**: DB内にバイナリ保存

**将来拡張**:
- Amazon S3等のオブジェクトストレージ
- DBにはパスのみ保存

### 6.7 互換性

**ブラウザ対応**:
- Chrome: 最新版
- Firefox: 最新版
- Safari: 最新版
- Edge: 最新版

**モバイル対応**:
- レスポンシブデザイン
- タッチ操作対応

---

## 付録

### A. データモデル図

データモデルの詳細は `DATA_MODEL.md` を参照してください。

### B. 用語集

| 用語 | 説明 |
|-----|------|
| 取引先 | システムを利用する顧客企業 |
| グループ | 取引先単位の組織 |
| グループメンバー | 取引先の担当者 |
| キャビネット | 文書管理の最上位階層 |
| フォルダ | 文書を格納する階層構造 |
| 文書 | 請求書PDFファイル |
| 版数 | 同一ファイル名の更新履歴 |
| グループパスワード | PDF暗号化用のパスワード |

### C. 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|----------|------|---------|-------|
| 1.0 | 2024-12-21 | 初版作成 | システム開発チーム |

---

**文書終わり**
