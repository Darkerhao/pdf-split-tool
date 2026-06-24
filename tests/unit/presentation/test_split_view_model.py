"""Unit tests for SplitViewModel"""
import unittest
from unittest.mock import Mock, MagicMock
from presentation.view_models.split_view_model import SplitViewModel
from application.dtos.split_result import SplitResult
from application.dtos.preview_result import PreviewResult, PreviewItem


class TestSplitViewModel(unittest.TestCase):
    """Test cases for SplitViewModel"""

    def setUp(self):
        """Set up test fixtures"""
        self.split_by_ranges_use_case = Mock()
        self.split_by_chapters_use_case = Mock()
        self.split_each_page_use_case = Mock()
        self.preview_use_case = Mock()

        self.view_model = SplitViewModel(
            self.split_by_ranges_use_case,
            self.split_by_chapters_use_case,
            self.split_each_page_use_case,
            self.preview_use_case
        )

    def test_property_changed_notification(self):
        """Test that property changes trigger notifications"""
        # Arrange
        callback = Mock()
        self.view_model.subscribe_property_changed(callback)

        # Act
        self.view_model.input_file = "test.pdf"

        # Assert
        # Note: Setting input_file also auto-sets output_dir, so we get 2 notifications
        self.assertEqual(callback.call_count, 2)
        # First call should be for input_file
        self.assertEqual(callback.call_args_list[0][0], ("input_file", "test.pdf"))

    def test_split_by_ranges_success(self):
        """Test successful split by ranges"""
        # Arrange
        self.split_by_ranges_use_case.execute.return_value = SplitResult.create_success(
            ["output1.pdf", "output2.pdf"]
        )

        completed_callback = Mock()
        self.view_model.subscribe_event("split_completed", completed_callback)

        self.view_model.input_file = "test.pdf"
        self.view_model.output_dir = "output"
        self.view_model.ranges = "1-3, 5-7"

        # Act
        self.view_model.split_by_ranges()

        # Assert
        self.split_by_ranges_use_case.execute.assert_called_once()
        completed_callback.assert_called_once()
        args = completed_callback.call_args[0]
        self.assertTrue(args[0])  # success

    def test_split_by_ranges_validation_failure(self):
        """Test split with missing input file"""
        # Arrange
        completed_callback = Mock()
        self.view_model.subscribe_event("split_completed", completed_callback)

        # No input file set

        # Act
        self.view_model.split_by_ranges()

        # Assert
        self.split_by_ranges_use_case.execute.assert_not_called()
        completed_callback.assert_called_once()
        args = completed_callback.call_args[0]
        self.assertFalse(args[0])  # not success

    def test_is_busy_during_operation(self):
        """Test that is_busy is set during operation"""
        # Arrange
        self.split_by_ranges_use_case.execute.return_value = SplitResult.create_success([])

        self.view_model.input_file = "test.pdf"
        self.view_model.output_dir = "output"
        self.view_model.ranges = "1-3"

        property_changes = []

        def track_changes(prop, value):
            if prop == "is_busy":
                property_changes.append(value)

        self.view_model.subscribe_property_changed(track_changes)

        # Act
        self.view_model.split_by_ranges()

        # Assert
        # Should be set to True, then False
        self.assertEqual(property_changes, [True, False])

    def test_preview_split(self):
        """Test preview functionality"""
        # Arrange
        preview_result = PreviewResult(
            items=[
                PreviewItem("test_1-3.pdf", "1-3", 3),
                PreviewItem("test_5-7.pdf", "5-7", 3)
            ],
            total_files=2
        )
        self.preview_use_case.preview_by_ranges.return_value = preview_result

        preview_callback = Mock()
        self.view_model.subscribe_event("preview_updated", preview_callback)

        self.view_model.input_file = "test.pdf"
        self.view_model.ranges = "1-3, 5-7"

        # Act
        self.view_model.preview_split()

        # Assert
        self.preview_use_case.preview_by_ranges.assert_called_once()
        preview_callback.assert_called_once_with(preview_result)


if __name__ == '__main__':
    unittest.main()
