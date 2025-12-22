"""PDF暗号化ユーティリティ"""
import io
from PyPDF2 import PdfReader, PdfWriter


def encrypt_pdf(pdf_data: bytes, password: str) -> bytes:
    """
    PDFファイルを暗号化する
    
    Args:
        pdf_data: PDFファイルのバイナリデータ
        password: 暗号化パスワード
    
    Returns:
        暗号化されたPDFのバイナリデータ
    """
    try:
        # 入力PDFを読み込み
        pdf_reader = PdfReader(io.BytesIO(pdf_data))
        pdf_writer = PdfWriter()
        
        # すべてのページをコピー
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # パスワードで暗号化
        pdf_writer.encrypt(
            user_password=password,
            owner_password=password,
            use_128bit=True
        )
        
        # 暗号化されたPDFをバイト配列に出力
        output = io.BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        return output.read()
    
    except Exception as e:
        raise Exception(f'PDF暗号化エラー: {str(e)}')


def is_pdf_encrypted(pdf_data: bytes) -> bool:
    """
    PDFファイルが暗号化されているか確認する
    
    Args:
        pdf_data: PDFファイルのバイナリデータ
    
    Returns:
        True: 暗号化されている, False: 暗号化されていない
    """
    try:
        pdf_reader = PdfReader(io.BytesIO(pdf_data))
        return pdf_reader.is_encrypted
    except Exception:
        return False
