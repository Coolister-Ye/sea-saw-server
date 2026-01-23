"""
Tests for file upload path generation
"""
import os
from datetime import datetime
from django.test import TestCase
from sea_saw_crm.utils import (
    get_upload_path,
    production_file_path,
    payment_attachment_path,
)


class FileUploadPathTestCase(TestCase):
    """Test file upload path generation"""

    def test_get_upload_path_structure(self):
        """Test that upload path has correct structure"""
        filename = "invoice.pdf"
        path = get_upload_path(None, filename, subfolder="test")

        # Should contain subfolder
        self.assertTrue(path.startswith("test/"))

        # Should contain date folders
        now = datetime.now()
        date_path = now.strftime("%Y/%m/%d")
        self.assertIn(date_path, path)

        # Should preserve extension
        self.assertTrue(path.endswith(".pdf"))

        # Should contain original filename
        self.assertIn("invoice", path)

    def test_unique_filenames(self):
        """Test that multiple uploads generate unique paths"""
        filename = "same_file.pdf"

        path1 = get_upload_path(None, filename, subfolder="test")
        path2 = get_upload_path(None, filename, subfolder="test")

        # Paths should be different due to UUID
        self.assertNotEqual(path1, path2)

    def test_production_file_path(self):
        """Test production file path generation"""
        filename = "production_plan.xlsx"
        path = production_file_path(None, filename)

        self.assertTrue(path.startswith("production_files/"))
        self.assertTrue(path.endswith(".xlsx"))
        self.assertIn("production_plan", path)

    def test_payment_attachment_path(self):
        """Test payment attachment path generation"""
        filename = "bank_slip.jpg"
        path = payment_attachment_path(None, filename)

        self.assertTrue(path.startswith("payment_attachments/"))
        self.assertTrue(path.endswith(".jpg"))
        self.assertIn("bank_slip", path)

    def test_special_characters_in_filename(self):
        """Test handling of special characters in filename"""
        filename = "file with spaces & special#chars.pdf"
        path = get_upload_path(None, filename, subfolder="test")

        # Should still work without errors
        self.assertTrue(path.endswith(".pdf"))
        self.assertIn("test/", path)

    def test_no_extension_filename(self):
        """Test handling of filename without extension"""
        filename = "README"
        path = get_upload_path(None, filename, subfolder="test")

        # Should handle files without extension
        self.assertIn("README", path)
        self.assertTrue(path.startswith("test/"))
