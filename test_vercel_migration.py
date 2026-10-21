"""
Comprehensive Test Suite for Vercel Deployment & Storage Migration.
Validates:
1. Safe startup without OSError under simulated Vercel (VERCEL=1, read-only root)
2. Storage service detection (is_cloudinary_id logic for all path patterns)
3. Cloudinary signed private download URL generation
4. TiDB TLS connection with certifi
5. Route functionality and backward compatibility (graceful fallback on old paths)
6. App entrypoints (app.py and api/index.py)
"""
import os
import sys
import unittest
import tempfile

class TestVercelMigration(unittest.TestCase):

    def test_01_storage_service_path_detection(self):
        """Test is_cloudinary_id distinguishes old paths from Cloudinary IDs."""
        from services.storage_service import is_cloudinary_id

        # Local Windows paths -> False
        self.assertFalse(is_cloudinary_id(r"C:\Users\HP\Documents\uploads\resumes\1\test.pdf"))
        self.assertFalse(is_cloudinary_id(r"D:\uploads\reports\1\test.pdf"))
        
        # Local Unix paths -> False
        self.assertFalse(is_cloudinary_id("/var/task/uploads/resumes/1/test.pdf"))
        self.assertFalse(is_cloudinary_id("/tmp/uploads/test.pdf"))
        
        # Relative local paths -> False
        self.assertFalse(is_cloudinary_id("uploads/resumes/1/test.pdf"))
        self.assertFalse(is_cloudinary_id("uploads/reports/1/test.pdf"))
        self.assertFalse(is_cloudinary_id("photos/avatar.jpg"))
        self.assertFalse(is_cloudinary_id(r"uploads\resumes\1\test.pdf"))
        
        # URLs -> False
        self.assertFalse(is_cloudinary_id("https://res.cloudinary.com/demo/image/upload/sample.jpg"))
        self.assertFalse(is_cloudinary_id("http://example.com/file.pdf"))
        
        # Empty/None -> False
        self.assertFalse(is_cloudinary_id(""))
        self.assertFalse(is_cloudinary_id(None))
        
        # Cloudinary public IDs -> True
        self.assertTrue(is_cloudinary_id("resumes/1/3a8b4c2e1f0a"))
        self.assertTrue(is_cloudinary_id("reports/1/career_a1b2c3d4"))
        self.assertTrue(is_cloudinary_id("photos/1/avatar_123"))

    def test_02_signed_url_generation(self):
        """Test Cloudinary private signed URL generation logic."""
        import cloudinary
        from services.storage_service import get_private_download_url
        
        # Configure with dummy test credentials
        cloudinary.config(cloud_name='test_cloud', api_key='111222333', api_secret='dummy_secret', secure=True)
        url = get_private_download_url("resumes/5/sample_id", "pdf", expires_in_seconds=300)
        
        self.assertIn("https://api.cloudinary.com/v1_1/test_cloud/raw/download", url)
        self.assertIn("public_id=resumes%2F5%2Fsample_id", url)
        self.assertIn("type=private", url)
        self.assertIn("signature=", url)
        self.assertIn("expires_at=", url)

    def test_03_temp_dir_writable(self):
        """Test get_temp_dir returns a writable directory."""
        from services.storage_service import get_temp_dir
        tdir = get_temp_dir()
        self.assertTrue(os.path.exists(tdir))
        test_file = os.path.join(tdir, "write_test.txt")
        with open(test_file, "w") as f:
            f.write("writable test")
        self.assertTrue(os.path.exists(test_file))
        os.remove(test_file)

    def test_04_app_startup_under_vercel_mode(self):
        """Test create_app starts cleanly when VERCEL=1 is set."""
        old_vercel = os.environ.get('VERCEL')
        old_config = os.environ.get('FLASK_CONFIG')
        try:
            os.environ['VERCEL'] = '1'
            os.environ['FLASK_CONFIG'] = 'production'
            if not os.environ.get('SECRET_KEY'):
                os.environ['SECRET_KEY'] = 'test-secret-key'

            from app import create_app
            app = create_app('production')
            self.assertFalse(app.debug)
            self.assertTrue(app.config['SESSION_COOKIE_SECURE'])
            self.assertTrue(app.config['UPLOAD_FOLDER'].startswith(tempfile.gettempdir()))
        finally:
            if old_vercel is not None:
                os.environ['VERCEL'] = old_vercel
            else:
                os.environ.pop('VERCEL', None)
            if old_config is not None:
                os.environ['FLASK_CONFIG'] = old_config
            else:
                os.environ.pop('FLASK_CONFIG', None)

    def test_05_api_index_entrypoint(self):
        """Test api/index.py imports and exposes app cleanly."""
        from api.index import app as vercel_app
        self.assertIsNotNone(vercel_app)
        self.assertEqual(vercel_app.name, 'app')

    def test_06_database_tls_connection(self):
        """Test database connection with certifi TLS to TiDB."""
        from app import create_app
        from database.db import get_db, close_db
        app = create_app('development')
        with app.app_context():
            try:
                db = get_db()
                self.assertTrue(db.is_connected())
            finally:
                close_db()

    def test_07_resume_and_report_download_fallback(self):
        """Test download routes return graceful redirect/flash for non-existent legacy paths."""
        from app import create_app
        from database.db import close_db
        app = create_app('development')
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = 999999
            sess['user_name'] = 'Test User'

        # Download of non-existent resume ID -> 302 redirect with flash (not 500)
        res = client.get('/resumes/download/999999')
        self.assertEqual(res.status_code, 302)

        # Download of non-existent report ID -> 302 redirect with flash (not 500)
        res_rep = client.get('/reports/download/999999')
        self.assertEqual(res_rep.status_code, 302)
        
        with app.app_context():
            close_db()

    def test_08_startup_never_touches_var_task(self):
        """Verify startup never attempts to create directories inside /var/task even if UPLOAD_FOLDER contains it."""
        from unittest.mock import patch
        from app import create_app
        import config

        # Simulate UPLOAD_FOLDER being set to /var/task/uploads
        with patch.object(config.Config, 'UPLOAD_FOLDER', '/var/task/uploads'):
            with patch('os.makedirs') as mock_makedirs:
                app = create_app('production')
                # Verify os.makedirs was never called on /var/task
                for call_args in mock_makedirs.call_args_list:
                    path_arg = call_args[0][0] if call_args[0] else ''
                    self.assertFalse(str(path_arg).startswith('/var/task'), f"Attempted to make dir in {path_arg}")


if __name__ == '__main__':
    unittest.main()
