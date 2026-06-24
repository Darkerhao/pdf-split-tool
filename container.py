"""Dependency Injection Container - Wires up all layers"""
from infrastructure.repositories.pypdf_repository import PyPDFRepository
from infrastructure.repositories.json_settings_repository import JSONSettingsRepository
from infrastructure.services.pdf_splitter_service import PyPDFSplitter, PyPDFMerger
from infrastructure.adapters.epub_adapter import CompositeEPUBConverter, PythonEPUBAdapter
from infrastructure.adapters.calibre_adapter import CalibreAdapter

from application.use_cases.split_pdf_by_ranges import SplitPDFByRangesUseCase
from application.use_cases.split_pdf_by_chapters import SplitPDFByChaptersUseCase
from application.use_cases.split_pdf_each_page import SplitPDFEachPageUseCase
from application.use_cases.merge_pdfs import MergePDFsUseCase
from application.use_cases.convert_epub import ConvertEPUBUseCase
from application.use_cases.preview_split import PreviewSplitUseCase
from application.services.app_state_service import AppStateService

from presentation.view_models.split_view_model import SplitViewModel
from presentation.view_models.merge_view_model import MergeViewModel
from presentation.view_models.epub_view_model import EPUBViewModel
from presentation.view_models.app_view_model import AppViewModel


class Container:
    """
    Dependency injection container

    Creates and wires up all dependencies across layers.
    Follows the dependency inversion principle.
    """

    def __init__(self):
        """Initialize container and create all dependencies"""
        # Infrastructure Layer - Repositories
        self.document_repository = PyPDFRepository()
        self.settings_repository = JSONSettingsRepository()

        # Infrastructure Layer - Services
        self.pdf_splitter = PyPDFSplitter()
        self.pdf_merger = PyPDFMerger()

        # Infrastructure Layer - Adapters
        python_epub_adapter = PythonEPUBAdapter()
        calibre_adapter = CalibreAdapter()
        self.epub_converter = CompositeEPUBConverter([python_epub_adapter, calibre_adapter])

        # Application Layer - Services
        self.app_state_service = AppStateService(self.settings_repository)

        # Application Layer - Use Cases
        self.split_by_ranges_use_case = SplitPDFByRangesUseCase(
            self.document_repository,
            self.pdf_splitter
        )

        self.split_by_chapters_use_case = SplitPDFByChaptersUseCase(
            self.document_repository,
            self.pdf_splitter
        )

        self.split_each_page_use_case = SplitPDFEachPageUseCase(
            self.document_repository,
            self.pdf_splitter
        )

        self.merge_pdfs_use_case = MergePDFsUseCase(
            self.pdf_merger
        )

        self.convert_epub_use_case = ConvertEPUBUseCase(
            self.epub_converter
        )

        self.preview_split_use_case = PreviewSplitUseCase(
            self.document_repository
        )

        # Presentation Layer - View Models
        self.split_view_model = SplitViewModel(
            self.split_by_ranges_use_case,
            self.split_by_chapters_use_case,
            self.split_each_page_use_case,
            self.preview_split_use_case
        )

        self.merge_view_model = MergeViewModel(
            self.merge_pdfs_use_case
        )

        self.epub_view_model = EPUBViewModel(
            self.convert_epub_use_case
        )

        self.app_view_model = AppViewModel(
            self.app_state_service
        )


# Global container instance
_container = None


def get_container() -> Container:
    """Get or create global container instance"""
    global _container
    if _container is None:
        _container = Container()
    return _container


def reset_container() -> None:
    """Reset container (useful for testing)"""
    global _container
    _container = None
