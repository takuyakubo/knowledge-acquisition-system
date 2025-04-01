"""
arXivコネクタの例外クラス定義

このモジュールは、arXivコネクタで使用される例外クラスを定義します。
"""


class ArxivConnectorError(Exception):
    """arXivコネクタのベースエラークラス"""
    pass


class ArxivAPIError(ArxivConnectorError):
    """arXiv APIとの通信エラー"""
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"arXiv API error ({status_code}): {message}")


class PDFDownloadError(ArxivConnectorError):
    """PDF取得エラー"""
    pass


class TextExtractionError(ArxivConnectorError):
    """テキスト抽出エラー"""
    pass


class DatabaseError(ArxivConnectorError):
    """データベース操作エラー"""
    pass


class SegmentationError(ArxivConnectorError):
    """テキストセグメント分割エラー"""
    pass


class EntityExtractionError(ArxivConnectorError):
    """エンティティ抽出エラー"""
    pass


class RelationExtractionError(ArxivConnectorError):
    """関係抽出エラー"""
    pass


class DataNotFoundError(ArxivConnectorError):
    """データ検索エラー"""
    pass