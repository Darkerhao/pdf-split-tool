"""领域异常"""


class DomainException(Exception):
    """领域异常基类"""
    pass


class InvalidPageRangeError(DomainException):
    """无效的页码范围异常"""
    pass


class DocumentNotFoundError(DomainException):
    """文档未找到异常"""
    pass


class InvalidDocumentFormatError(DomainException):
    """无效的文档格式异常"""
    pass


class ChaptersNotFoundError(DomainException):
    """章节信息未找到异常"""
    pass


class ConversionFailedError(DomainException):
    """转换失败异常"""
    pass
