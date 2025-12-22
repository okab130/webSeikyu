# WEB請求書システム API利用手順書

## 目次
1. [概要](#概要)
2. [前提条件](#前提条件)
3. [認証](#認証)
4. [API仕様](#api仕様)
5. [利用手順](#利用手順)
6. [サンプルコード](#サンプルコード)
7. [エラーハンドリング](#エラーハンドリング)
8. [トラブルシューティング](#トラブルシューティング)

---

## 概要

WEB請求書システムAPIは、請求書発行システムから請求書PDFを自動登録するためのREST APIです。

### 主な機能
- APIユーザーによる認証
- 請求書PDFファイルのアップロード
- 自動フォルダ管理（取引先/年度/月の階層構造）
- 版数管理（同一ファイル名の複数バージョン対応）
- メール通知（取引先担当者への自動通知）

### API仕様
- **プロトコル**: HTTP/HTTPS
- **認証方式**: セッションベース認証（Cookie）
- **リクエスト形式**: JSON / multipart/form-data
- **レスポンス形式**: JSON
- **文字コード**: UTF-8

---

## 前提条件

### 必要な情報
1. **APIユーザーアカウント**
   - メールアドレス
   - パスワード
   
2. **取引先コード**
   - 5桁の数字（例: `00001`）
   - システム管理者から事前に発行

3. **請求書PDFファイル**
   - ファイル名規則: `{文書種別}-{請求書番号}-{請求日YYYYMMDD}.PDF`
   - 最大サイズ: **20MB**
   - 形式: PDF

### システム要件
- Python 3.8以上、または
- cURL、または
- 任意のHTTPクライアント（Postman、Insomnia等）

---

## 認証

### APIユーザー作成（管理者が実施）

管理者がDjango管理画面またはシェルで作成：

```python
# Django shell
python manage.py shell

from documents.models import User

# APIユーザー作成
api_user = User.objects.create(
    email='api@yourcompany.com',
    user_type='api',
    full_name='請求書発行システム',
    is_active=True
)
api_user.set_password('your_secure_password')
api_user.save()
```

### テスト用アカウント

開発・テスト環境では以下のアカウントが利用可能：

```
メールアドレス: api@example.com
パスワード: api123
```

---

## API仕様

### ベースURL

```
開発環境: http://localhost:8000
本番環境: https://your-domain.com
```

### エンドポイント一覧

| エンドポイント | メソッド | 認証 | 説明 |
|--------------|---------|------|------|
| `/api/login/` | POST | 不要 | APIログイン |
| `/api/logout/` | POST | 必要 | APIログアウト |
| `/api/documents/upload/` | POST | 必要 | 請求書PDF登録 |

---

## 利用手順

### ステップ1: APIログイン

#### リクエスト

```http
POST /api/login/ HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "email": "api@example.com",
  "password": "api123"
}
```

#### レスポンス（成功）

```json
{
  "status": "success",
  "message": "ログインに成功しました"
}
```

#### レスポンス（失敗）

```json
{
  "status": "error",
  "message": "認証に失敗しました"
}
```

**重要**: レスポンスヘッダーの`Set-Cookie`に含まれるセッションIDを保存してください。

---

### ステップ2: 請求書PDFアップロード

#### ファイル名規則

請求書PDFファイル名は以下の形式に従ってください：

```
{文書種別}-{請求書番号}-{請求日YYYYMMDD}.PDF
```

**文書種別**:
- `月次請求書` - 月次請求書
- `随時請求書` - 随時請求書

**例**:
- ✅ `月次請求書-INV-00001-202412-001-20241220.PDF`
- ✅ `随時請求書-INV-SP-00001-001-20241215.PDF`
- ❌ `invoice.pdf` （形式が不正）
- ❌ `請求書-20241220.PDF` （要素が不足）

#### リクエスト

```http
POST /api/documents/upload/ HTTP/1.1
Host: localhost:8000
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary
Cookie: sessionid=<セッションID>

------WebKitFormBoundary
Content-Disposition: form-data; name="client_code"

00001
------WebKitFormBoundary
Content-Disposition: form-data; name="encrypt_flag"

true
------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="月次請求書-INV001-20241220.PDF"
Content-Type: application/pdf

<PDFバイナリデータ>
------WebKitFormBoundary--
```

#### パラメータ

| パラメータ名 | 型 | 必須 | 説明 |
|------------|-----|------|------|
| `client_code` | string | ✓ | 取引先コード（5桁） |
| `encrypt_flag` | string | - | 暗号化フラグ（`true`/`false`、デフォルト: `false`） |
| `file` | file | ✓ | 請求書PDFファイル（最大20MB） |

#### レスポンス（成功）

```json
{
  "status": "success",
  "message": "文書を登録しました",
  "document_id": 123,
  "version": 1
}
```

**version**: 同じファイル名で複数回アップロードすると自動的にインクリメントされます。

#### レスポンス（エラー）

```json
{
  "status": "error",
  "message": "ファイルサイズが上限（20MB）を超えています"
}
```

---

### ステップ3: APIログアウト（オプション）

#### リクエスト

```http
POST /api/logout/ HTTP/1.1
Host: localhost:8000
Cookie: sessionid=<セッションID>
```

#### レスポンス

```json
{
  "status": "success",
  "message": "ログアウトしました"
}
```

---

## サンプルコード

### cURLを使用した例

#### Linux/Mac向け

##### 1. ログイン

```bash
#!/bin/bash

# セッション保存用のCookieファイル
COOKIE_FILE="cookies.txt"

# ログイン
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"api@example.com","password":"api123"}' \
  -c $COOKIE_FILE \
  -v

# レスポンス確認
echo "ログイン完了"
```

##### 2. PDFアップロード

```bash
#!/bin/bash

COOKIE_FILE="cookies.txt"

# PDFファイルをアップロード
curl -X POST http://localhost:8000/api/documents/upload/ \
  -b $COOKIE_FILE \
  -F "client_code=00001" \
  -F "encrypt_flag=true" \
  -F "file=@月次請求書-INV001-20241220.PDF" \
  -v

echo "アップロード完了"
```

##### 3. ログアウト

```bash
#!/bin/bash

COOKIE_FILE="cookies.txt"

# ログアウト
curl -X POST http://localhost:8000/api/logout/ \
  -b $COOKIE_FILE \
  -v

# Cookieファイルを削除
rm $COOKIE_FILE

echo "ログアウト完了"
```

---

#### Windows向け

##### 1. ログイン（PowerShell）

```powershell
# PowerShellスクリプト
# login.ps1

# セッション保存用のCookieファイル
$COOKIE_FILE = "cookies.txt"

# ログイン
curl.exe -X POST "http://localhost:8000/api/login/" `
  -H "Content-Type: application/json" `
  -d "{`"email`":`"api@example.com`",`"password`":`"api123`"}" `
  -c $COOKIE_FILE `
  -v

Write-Host "ログイン完了"
```

##### 2. PDFアップロード（PowerShell）

```powershell
# PowerShellスクリプト
# upload.ps1

$COOKIE_FILE = "cookies.txt"

# PDFファイルをアップロード
curl.exe -X POST "http://localhost:8000/api/documents/upload/" `
  -b $COOKIE_FILE `
  -F "client_code=00001" `
  -F "encrypt_flag=true" `
  -F "file=@月次請求書-INV001-20241220.PDF" `
  -v

Write-Host "アップロード完了"
```

##### 3. ログアウト（PowerShell）

```powershell
# PowerShellスクリプト
# logout.ps1

$COOKIE_FILE = "cookies.txt"

# ログアウト
curl.exe -X POST "http://localhost:8000/api/logout/" `
  -b $COOKIE_FILE `
  -v

# Cookieファイルを削除
Remove-Item $COOKIE_FILE -ErrorAction SilentlyContinue

Write-Host "ログアウト完了"
```

##### 4. 統合スクリプト（PowerShell）

```powershell
# PowerShellスクリプト
# upload_invoice.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$ClientCode,
    
    [Parameter(Mandatory=$true)]
    [string]$PdfFile
)

# 設定
$API_BASE_URL = "http://localhost:8000"
$API_EMAIL = "api@example.com"
$API_PASSWORD = "api123"
$COOKIE_FILE = "cookies.txt"

# ファイル存在チェック
if (-not (Test-Path $PdfFile)) {
    Write-Host "エラー: ファイルが見つかりません: $PdfFile" -ForegroundColor Red
    exit 1
}

try {
    # 1. ログイン
    Write-Host "=== ログイン中... ===" -ForegroundColor Cyan
    $loginJson = "{`"email`":`"$API_EMAIL`",`"password`":`"$API_PASSWORD`"}"
    $loginResponse = curl.exe -s -X POST "$API_BASE_URL/api/login/" `
        -H "Content-Type: application/json" `
        -d $loginJson `
        -c $COOKIE_FILE
    
    Write-Host $loginResponse
    
    if ($loginResponse -match '"status":"success"') {
        Write-Host "✓ ログイン成功" -ForegroundColor Green
    } else {
        Write-Host "✗ ログイン失敗" -ForegroundColor Red
        exit 1
    }
    
    # 2. PDFアップロード
    Write-Host ""
    Write-Host "=== PDFアップロード中... ===" -ForegroundColor Cyan
    $uploadResponse = curl.exe -s -X POST "$API_BASE_URL/api/documents/upload/" `
        -b $COOKIE_FILE `
        -F "client_code=$ClientCode" `
        -F "encrypt_flag=true" `
        -F "file=@$PdfFile"
    
    Write-Host $uploadResponse
    
    if ($uploadResponse -match '"status":"success"') {
        Write-Host "✓ アップロード成功" -ForegroundColor Green
        
        # document_idとversionを抽出
        if ($uploadResponse -match '"document_id":(\d+)') {
            $documentId = $matches[1]
            Write-Host "  - 文書ID: $documentId" -ForegroundColor Yellow
        }
        if ($uploadResponse -match '"version":(\d+)') {
            $version = $matches[1]
            Write-Host "  - 版数: $version" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✗ アップロード失敗" -ForegroundColor Red
        exit 1
    }
    
    # 3. ログアウト
    Write-Host ""
    Write-Host "=== ログアウト中... ===" -ForegroundColor Cyan
    $logoutResponse = curl.exe -s -X POST "$API_BASE_URL/api/logout/" `
        -b $COOKIE_FILE
    
    Write-Host $logoutResponse
    
    # Cookieファイルを削除
    Remove-Item $COOKIE_FILE -ErrorAction SilentlyContinue
    
    Write-Host ""
    Write-Host "=== 処理完了 ===" -ForegroundColor Green
    
} catch {
    Write-Host "エラー: $_" -ForegroundColor Red
    Remove-Item $COOKIE_FILE -ErrorAction SilentlyContinue
    exit 1
}
```

**使用方法（PowerShell）**:
```powershell
# スクリプトを実行
.\upload_invoice.ps1 -ClientCode "00001" -PdfFile "月次請求書-INV001-20241220.PDF"
```

---

##### 5. バッチファイル（Windows cmd）

```batch
@echo off
REM upload_invoice.bat
REM 使用方法: upload_invoice.bat <取引先コード> <PDFファイルパス>

setlocal

REM 設定
set API_BASE_URL=http://localhost:8000
set API_EMAIL=api@example.com
set API_PASSWORD=api123
set COOKIE_FILE=cookies.txt

REM 引数チェック
if "%~1"=="" (
    echo 使用方法: %~nx0 ^<取引先コード^> ^<PDFファイルパス^>
    echo 例: %~nx0 00001 月次請求書-INV001-20241220.PDF
    exit /b 1
)

if "%~2"=="" (
    echo 使用方法: %~nx0 ^<取引先コード^> ^<PDFファイルパス^>
    echo 例: %~nx0 00001 月次請求書-INV001-20241220.PDF
    exit /b 1
)

set CLIENT_CODE=%~1
set PDF_FILE=%~2

REM ファイル存在チェック
if not exist "%PDF_FILE%" (
    echo エラー: ファイルが見つかりません: %PDF_FILE%
    exit /b 1
)

REM 1. ログイン
echo === ログイン中... ===
curl.exe -s -X POST "%API_BASE_URL%/api/login/" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"%API_EMAIL%\",\"password\":\"%API_PASSWORD%\"}" ^
  -c %COOKIE_FILE% > login_response.txt

type login_response.txt
findstr /C:"\"status\":\"success\"" login_response.txt >nul
if %errorlevel% neq 0 (
    echo ✗ ログイン失敗
    del login_response.txt
    exit /b 1
)
echo ✓ ログイン成功
del login_response.txt

REM 2. PDFアップロード
echo.
echo === PDFアップロード中... ===
curl.exe -s -X POST "%API_BASE_URL%/api/documents/upload/" ^
  -b %COOKIE_FILE% ^
  -F "client_code=%CLIENT_CODE%" ^
  -F "encrypt_flag=true" ^
  -F "file=@%PDF_FILE%" > upload_response.txt

type upload_response.txt
findstr /C:"\"status\":\"success\"" upload_response.txt >nul
if %errorlevel% neq 0 (
    echo ✗ アップロード失敗
    del upload_response.txt
    del %COOKIE_FILE%
    exit /b 1
)
echo ✓ アップロード成功
del upload_response.txt

REM 3. ログアウト
echo.
echo === ログアウト中... ===
curl.exe -s -X POST "%API_BASE_URL%/api/logout/" ^
  -b %COOKIE_FILE% > logout_response.txt

type logout_response.txt
del logout_response.txt

REM Cookieファイルを削除
if exist %COOKIE_FILE% del %COOKIE_FILE%

echo.
echo === 処理完了 ===

endlocal
```

**使用方法（コマンドプロンプト）**:
```cmd
upload_invoice.bat 00001 月次請求書-INV001-20241220.PDF
```

---

##### Windows環境での注意点

**1. curl.exeを使用する**
```powershell
# PowerShellのInvoke-WebRequestではなく、curl.exeを明示的に使用
curl.exe -X POST ...
```

PowerShellには`curl`エイリアス（`Invoke-WebRequest`）がありますが、本物のcURLとは異なります。

**2. JSONのエスケープ**
```powershell
# ダブルクォートをバッククォートでエスケープ
-d "{`"email`":`"api@example.com`",`"password`":`"api123`"}"
```

**3. バックティック（`）で改行**
```powershell
# PowerShellでは行継続にバックティック（`）を使用
curl.exe -X POST "http://localhost:8000/api/login/" `
  -H "Content-Type: application/json" `
  -d "..."
```

**4. ファイルパス**
```powershell
# 相対パス
-F "file=@.\月次請求書-INV001-20241220.PDF"

# 絶対パス
-F "file=@C:\invoices\月次請求書-INV001-20241220.PDF"
```

**5. 文字コード**
```powershell
# PowerShellスクリプトをUTF-8 BOMなしで保存
# スクリプト内で日本語を使用する場合は重要
```

---

##### Windows PowerShell ISEでの実行例

```powershell
# PowerShell ISEで実行

# 1. スクリプトを保存
# upload_invoice.ps1として保存

# 2. 実行ポリシーを確認
Get-ExecutionPolicy

# 3. 必要に応じて実行ポリシーを変更（管理者権限）
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 4. スクリプトを実行
.\upload_invoice.ps1 -ClientCode "00001" -PdfFile "C:\invoices\月次請求書-INV001-20241220.PDF"
```

---

##### Linux/Mac統合スクリプト

```bash
#!/bin/bash

# 設定
API_BASE_URL="http://localhost:8000"
API_EMAIL="api@example.com"
API_PASSWORD="api123"
COOKIE_FILE="cookies.txt"

# 引数チェック
if [ $# -ne 2 ]; then
    echo "使用方法: $0 <取引先コード> <PDFファイルパス>"
    echo "例: $0 00001 月次請求書-INV001-20241220.PDF"
    exit 1
fi

CLIENT_CODE=$1
PDF_FILE=$2

# ファイル存在チェック
if [ ! -f "$PDF_FILE" ]; then
    echo "エラー: ファイルが見つかりません: $PDF_FILE"
    exit 1
fi

# 1. ログイン
echo "=== ログイン中... ==="
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/login/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$API_EMAIL\",\"password\":\"$API_PASSWORD\"}" \
  -c $COOKIE_FILE)

echo "$LOGIN_RESPONSE"

if echo "$LOGIN_RESPONSE" | grep -q '"status":"success"'; then
    echo "✓ ログイン成功"
else
    echo "✗ ログイン失敗"
    exit 1
fi

# 2. PDFアップロード
echo ""
echo "=== PDFアップロード中... ==="
UPLOAD_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/documents/upload/" \
  -b $COOKIE_FILE \
  -F "client_code=$CLIENT_CODE" \
  -F "encrypt_flag=true" \
  -F "file=@$PDF_FILE")

echo "$UPLOAD_RESPONSE"

if echo "$UPLOAD_RESPONSE" | grep -q '"status":"success"'; then
    echo "✓ アップロード成功"
    # document_idとversionを抽出
    DOCUMENT_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"document_id":[0-9]*' | cut -d':' -f2)
    VERSION=$(echo "$UPLOAD_RESPONSE" | grep -o '"version":[0-9]*' | cut -d':' -f2)
    echo "  - 文書ID: $DOCUMENT_ID"
    echo "  - 版数: $VERSION"
else
    echo "✗ アップロード失敗"
    exit 1
fi

# 3. ログアウト
echo ""
echo "=== ログアウト中... ==="
LOGOUT_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/logout/" \
  -b $COOKIE_FILE)

echo "$LOGOUT_RESPONSE"

# Cookieファイルを削除
rm -f $COOKIE_FILE

echo ""
echo "=== 処理完了 ==="
```

**使用方法**:
```bash
chmod +x upload_invoice.sh
./upload_invoice.sh 00001 月次請求書-INV001-20241220.PDF
```

---

### Pythonを使用した例

#### requests ライブラリ使用

```python
#!/usr/bin/env python3
import requests
import json
import sys

# 設定
API_BASE_URL = "http://localhost:8000"
API_EMAIL = "api@example.com"
API_PASSWORD = "api123"

class InvoiceAPIClient:
    def __init__(self, base_url, email, password):
        self.base_url = base_url
        self.email = email
        self.password = password
        self.session = requests.Session()
    
    def login(self):
        """APIログイン"""
        url = f"{self.base_url}/api/login/"
        data = {
            "email": self.email,
            "password": self.password
        }
        
        response = self.session.post(url, json=data)
        result = response.json()
        
        if result.get('status') == 'success':
            print("✓ ログイン成功")
            return True
        else:
            print(f"✗ ログイン失敗: {result.get('message')}")
            return False
    
    def upload_document(self, client_code, file_path, encrypt_flag=True):
        """請求書PDFアップロード"""
        url = f"{self.base_url}/api/documents/upload/"
        
        # ファイル読み込み
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path, f, 'application/pdf')
            }
            data = {
                'client_code': client_code,
                'encrypt_flag': 'true' if encrypt_flag else 'false'
            }
            
            response = self.session.post(url, files=files, data=data)
        
        result = response.json()
        
        if result.get('status') == 'success':
            print("✓ アップロード成功")
            print(f"  - 文書ID: {result.get('document_id')}")
            print(f"  - 版数: {result.get('version')}")
            return True
        else:
            print(f"✗ アップロード失敗: {result.get('message')}")
            return False
    
    def logout(self):
        """APIログアウト"""
        url = f"{self.base_url}/api/logout/"
        response = self.session.post(url)
        result = response.json()
        
        if result.get('status') == 'success':
            print("✓ ログアウト成功")
            return True
        else:
            print(f"✗ ログアウト失敗: {result.get('message')}")
            return False

def main():
    # 引数チェック
    if len(sys.argv) != 3:
        print("使用方法: python upload_invoice.py <取引先コード> <PDFファイルパス>")
        print("例: python upload_invoice.py 00001 月次請求書-INV001-20241220.PDF")
        sys.exit(1)
    
    client_code = sys.argv[1]
    pdf_file = sys.argv[2]
    
    # APIクライアント初期化
    client = InvoiceAPIClient(API_BASE_URL, API_EMAIL, API_PASSWORD)
    
    try:
        # 1. ログイン
        print("=== ログイン中... ===")
        if not client.login():
            sys.exit(1)
        
        # 2. PDFアップロード
        print("\n=== PDFアップロード中... ===")
        if not client.upload_document(client_code, pdf_file):
            sys.exit(1)
        
        # 3. ログアウト
        print("\n=== ログアウト中... ===")
        client.logout()
        
        print("\n=== 処理完了 ===")
        
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**使用方法**:
```bash
pip install requests
python upload_invoice.py 00001 月次請求書-INV001-20241220.PDF
```

#### バッチ処理例

```python
#!/usr/bin/env python3
import os
import glob
from pathlib import Path
from upload_invoice import InvoiceAPIClient

# 設定
API_BASE_URL = "http://localhost:8000"
API_EMAIL = "api@example.com"
API_PASSWORD = "api123"
PDF_DIRECTORY = "./invoices"  # PDFファイルが格納されているディレクトリ

def main():
    # APIクライアント初期化
    client = InvoiceAPIClient(API_BASE_URL, API_EMAIL, API_PASSWORD)
    
    # ログイン
    print("=== ログイン中... ===")
    if not client.login():
        return
    
    # PDFファイルを検索
    pdf_files = glob.glob(f"{PDF_DIRECTORY}/*.PDF") + glob.glob(f"{PDF_DIRECTORY}/*.pdf")
    
    if not pdf_files:
        print(f"警告: {PDF_DIRECTORY} にPDFファイルが見つかりません")
        return
    
    print(f"\n{len(pdf_files)}件のPDFファイルを処理します\n")
    
    success_count = 0
    error_count = 0
    
    # 各ファイルをアップロード
    for pdf_file in pdf_files:
        file_name = os.path.basename(pdf_file)
        print(f"=== 処理中: {file_name} ===")
        
        # ファイル名から取引先コードを抽出（例: 月次請求書-INV-00001-202412-001-20241220.PDF）
        # 実際のファイル名形式に合わせて調整してください
        try:
            # ここでは単純化のため、client_codeは固定値を使用
            client_code = "00001"  # 実際はファイル名から抽出
            
            if client.upload_document(client_code, pdf_file):
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            print(f"✗ エラー: {e}")
            error_count += 1
        
        print()
    
    # ログアウト
    print("=== ログアウト中... ===")
    client.logout()
    
    # サマリー表示
    print("\n=== 処理結果 ===")
    print(f"成功: {success_count}件")
    print(f"失敗: {error_count}件")
    print(f"合計: {len(pdf_files)}件")

if __name__ == "__main__":
    main()
```

---

## エラーハンドリング

### エラーレスポンス形式

すべてのエラーレスポンスは以下の形式で返されます：

```json
{
  "status": "error",
  "message": "エラーの詳細メッセージ"
}
```

### HTTPステータスコード

| コード | 説明 |
|-------|------|
| 200 | 成功 |
| 400 | リクエストエラー（パラメータ不足、形式不正） |
| 401 | 認証エラー |
| 500 | サーバーエラー |

### よくあるエラーと対処法

#### 1. 認証エラー

**エラーメッセージ**: `"認証が必要です"`

**原因**:
- ログインしていない
- セッションが切れている
- Cookieが送信されていない

**対処法**:
- 先に `/api/login/` でログインする
- Cookieを正しく保存・送信する

---

#### 2. ファイル名形式エラー

**エラーメッセージ**: `"ファイル名の形式が不正です"`

**原因**:
- ファイル名が規則に従っていない
- ハイフン（`-`）の数が不足

**対処法**:
- ファイル名を `{文書種別}-{請求書番号}-{請求日}.PDF` の形式に修正

**正しい例**:
```
月次請求書-INV001-20241220.PDF
随時請求書-INV-SP-001-20241215.PDF
```

---

#### 3. ファイルサイズ超過

**エラーメッセージ**: `"ファイルサイズが上限（20MB）を超えています"`

**原因**:
- PDFファイルが20MBを超えている

**対処法**:
- PDFを圧縮する
- 画像の解像度を下げる
- 不要なページを削除する

---

#### 4. 必須パラメータ不足

**エラーメッセージ**: `"必須パラメータが不足しています"`

**原因**:
- `client_code` または `file` が指定されていない

**対処法**:
- すべての必須パラメータを指定する

---

#### 5. 文書種別エラー

**エラーメッセージ**: `"文書種別が不正です"`

**原因**:
- ファイル名の先頭が「月次請求書」または「随時請求書」でない

**対処法**:
- ファイル名を修正する

---

## トラブルシューティング

### デバッグ方法

#### 1. 詳細なログ出力

cURLで`-v`オプションを使用：

```bash
curl -v -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"api@example.com","password":"api123"}'
```

#### 2. レスポンスの確認

```bash
# レスポンスを整形して表示
curl -s -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"api@example.com","password":"api123"}' \
  | python -m json.tool
```

#### 3. Cookieの確認

```bash
# Cookie内容を確認
cat cookies.txt
```

---

### よくある質問（FAQ）

#### Q1: セッションの有効期限は？

**A**: デフォルトでは2週間です。長時間使用しない場合は再ログインが必要です。

---

#### Q2: 同時に複数のファイルをアップロードできますか？

**A**: いいえ。1回のリクエストで1ファイルのみです。複数ファイルは繰り返しAPIを呼び出してください。

---

#### Q3: 同じファイルを複数回アップロードするとどうなりますか？

**A**: 版数が自動的にインクリメントされ、最新版として登録されます。古い版も保持されます。

---

#### Q4: 取引先コードが間違っていた場合は？

**A**: フォルダが自動作成されますが、正しい取引先に紐づかないため、管理者に削除を依頼してください。

---

#### Q5: アップロード後に取引先担当者に通知されますか？

**A**: はい。取引先のグループメンバー全員にメール通知が送信されます。

---

## 補足資料

### ファイル名命名規則の詳細

#### 文書種別

| 文書種別 | 説明 |
|---------|------|
| 月次請求書 | 定期的な月次請求書 |
| 随時請求書 | スポット・臨時の請求書 |

#### 請求書番号

- 自由形式（英数字・ハイフン可）
- 例: `INV001`, `INV-00001-202412-001`

#### 請求日

- 形式: `YYYYMMDD`
- 例: `20241220` (2024年12月20日)

#### 完全な例

```
月次請求書-INV-00001-202412-001-20241220.PDF
└─┬──┘ └────┬────────────┘ └──┬──┘
  │          │                    └─ 請求日
  │          └─ 請求書番号
  └─ 文書種別
```

---

### サポート

技術的な問題や質問がある場合は、システム管理者にお問い合わせください。

---

**最終更新日**: 2024年12月20日
**バージョン**: 1.0
