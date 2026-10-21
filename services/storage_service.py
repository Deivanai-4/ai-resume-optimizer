"""
Storage Service for AI Career Intelligence Platform.
Supports persistent cloud storage via Cloudinary and local filesystem fallback.
Provides access control, short-lived signed URLs for private files (resumes, reports),
and public delivery for profile photos.
"""
import os
import time
import uuid
import tempfile
import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)


def get_temp_dir() -> str:
    """Return a writable directory for temporary file processing."""
    temp_dir = os.path.join(tempfile.gettempdir(), 'ai_career_temp')
    try:
        os.makedirs(temp_dir, exist_ok=True)
    except OSError:
        pass
    return temp_dir


def is_cloudinary_configured() -> bool:
    """Return True if Cloudinary credentials are provided via env or app config."""
    cfg = current_app.config if current_app else {}
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME') or cfg.get('CLOUDINARY_CLOUD_NAME')
    api_key = os.environ.get('CLOUDINARY_API_KEY') or cfg.get('CLOUDINARY_API_KEY')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET') or cfg.get('CLOUDINARY_API_SECRET')
    return bool(cloud_name and api_key and api_secret)


def configure_cloudinary():
    """Configure cloudinary library with available credentials."""
    import cloudinary
    cfg = current_app.config if current_app else {}
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME') or cfg.get('CLOUDINARY_CLOUD_NAME')
    api_key = os.environ.get('CLOUDINARY_API_KEY') or cfg.get('CLOUDINARY_API_KEY')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET') or cfg.get('CLOUDINARY_API_SECRET')
    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )


def is_cloudinary_id(path: str) -> bool:
    """
    Distinguishes a Cloudinary public_id from a local filesystem path.
    - Windows absolute paths: 'C:\\...' or has ':' as second character -> False
    - Unix absolute paths: starts with '/' -> False
    - Local relative paths: starts with 'uploads/' or single-segment 'photos/<filename>' -> False
    - Full URLs: starts with 'http://' or 'https://' -> False
    - Cloudinary public_ids: starts with 'resumes/' or 'reports/' (or multi-segment 'photos/user_id/uuid') -> True
    """
    if not path or not isinstance(path, str):
        return False
    norm = path.replace('\\', '/')
    if norm.startswith(('http://', 'https://')):
        return False
    if len(path) >= 2 and path[1] == ':':
        return False
    if path.startswith('/'):
        return False
    if norm.startswith('uploads/'):
        return False
    # Legacy photo relative paths are formatted as 'photos/<filename>' with 1 slash
    if norm.startswith('photos/') and norm.count('/') < 2:
        return False
    return norm.startswith(('resumes/', 'reports/', 'photos/'))


# ---------------------------------------------------------------------------
# Resumes (Private)
# ---------------------------------------------------------------------------

def upload_resume_file(file_obj_or_path, user_id: int, original_filename: str) -> str:
    """
    Upload a resume file.
    If Cloudinary is configured, uploads as a private raw asset and returns public_id.
    Otherwise saves to local upload folder and returns absolute local path.
    """
    if is_cloudinary_configured():
        configure_cloudinary()
        import cloudinary.uploader
        public_id = f"resumes/{user_id}/{uuid.uuid4().hex}"
        logger.info(f"Uploading resume for user {user_id} to Cloudinary as private asset: {public_id}")
        cloudinary.uploader.upload(
            file_obj_or_path,
            public_id=public_id,
            resource_type="raw",
            type="private"
        )
        return public_id
    else:
        # Local fallback
        upload_base = current_app.config.get("UPLOAD_FOLDER") or get_temp_dir()
        if upload_base.startswith('/var/task'):
            upload_base = get_temp_dir()
        resumes_dir = os.path.join(upload_base, 'resumes', str(user_id))
        os.makedirs(resumes_dir, exist_ok=True)
        from utils.helpers import generate_unique_filename
        filename = generate_unique_filename(original_filename)
        dest_path = os.path.join(resumes_dir, filename)
        
        if isinstance(file_obj_or_path, str):
            import shutil
            shutil.copyfile(file_obj_or_path, dest_path)
        else:
            file_obj_or_path.save(dest_path)
        return dest_path


def get_private_download_url(public_id: str, fmt: str, expires_in_seconds: int = 300) -> str:
    """Generate a time-limited signed download URL for a private raw Cloudinary asset."""
    configure_cloudinary()
    import cloudinary.utils
    clean_fmt = fmt.lstrip('.').lower()
    return cloudinary.utils.private_download_url(
        public_id=public_id,
        format=clean_fmt,
        resource_type="raw",
        type="private",
        expires_at=int(time.time()) + expires_in_seconds,
        attachment=True
    )


def fetch_resume_for_processing(file_path: str, file_type: str) -> tuple[str, bool]:
    """
    Ensure the resume file is accessible on disk for local parsers (pdfplumber, pypdf, python-docx).
    Returns (local_path, is_temporary).
    If is_temporary is True, caller should delete local_path after parsing.
    """
    if is_cloudinary_id(file_path):
        signed_url = get_private_download_url(file_path, file_type, expires_in_seconds=120)
        resp = requests.get(signed_url, timeout=30)
        resp.raise_for_status()
        
        ext = file_type.lstrip('.').lower()
        temp_file = os.path.join(get_temp_dir(), f"parse_{uuid.uuid4().hex}.{ext}")
        with open(temp_file, 'wb') as f:
            f.write(resp.content)
        return temp_file, True
    else:
        return file_path, False


# ---------------------------------------------------------------------------
# Reports (Private)
# ---------------------------------------------------------------------------

def upload_report_file(temp_pdf_path: str, user_id: int, report_type: str) -> str:
    """
    Upload a generated PDF report.
    If Cloudinary is configured, uploads as a private raw asset and returns public_id.
    Otherwise saves to local upload folder and returns local path.
    """
    if is_cloudinary_configured():
        configure_cloudinary()
        import cloudinary.uploader
        public_id = f"reports/{user_id}/{report_type.lower()}_{uuid.uuid4().hex[:8]}"
        logger.info(f"Uploading report for user {user_id} to Cloudinary: {public_id}")
        cloudinary.uploader.upload(
            temp_pdf_path,
            public_id=public_id,
            resource_type="raw",
            type="private"
        )
        return public_id
    else:
        upload_base = current_app.config.get("UPLOAD_FOLDER") or get_temp_dir()
        if upload_base.startswith('/var/task'):
            upload_base = get_temp_dir()
        reports_dir = os.path.join(upload_base, 'reports', str(user_id))
        os.makedirs(reports_dir, exist_ok=True)
        filename = f"{report_type.lower()}_report_{uuid.uuid4().hex[:8]}.pdf"
        dest_path = os.path.join(reports_dir, filename)
        import shutil
        shutil.copyfile(temp_pdf_path, dest_path)
        return dest_path


# ---------------------------------------------------------------------------
# Profile Photos (Public CDN)
# ---------------------------------------------------------------------------

def upload_profile_photo(file_obj, user_id: int) -> str:
    """
    Upload a user profile photo.
    If Cloudinary is configured, uploads to CDN with standard dimensions and returns secure URL.
    Otherwise saves locally and returns 'photos/<filename>'.
    """
    if is_cloudinary_configured():
        configure_cloudinary()
        import cloudinary.uploader
        public_id = f"photos/{user_id}/{uuid.uuid4().hex[:8]}"
        res = cloudinary.uploader.upload(
            file_obj,
            public_id=public_id,
            resource_type="image",
            type="upload",
            transformation=[
                {"width": 300, "height": 300, "crop": "fill", "gravity": "face"}
            ]
        )
        return res.get("secure_url") or res.get("url")
    else:
        upload_base = current_app.config.get("UPLOAD_FOLDER") or get_temp_dir()
        if upload_base.startswith('/var/task'):
            upload_base = get_temp_dir()
        photos_dir = os.path.join(upload_base, 'photos')
        os.makedirs(photos_dir, exist_ok=True)
        from utils.helpers import generate_unique_filename
        filename = generate_unique_filename(file_obj.filename)
        dest_path = os.path.join(photos_dir, filename)
        file_obj.save(dest_path)
        return f"photos/{filename}"


# ---------------------------------------------------------------------------
# Deletion
# ---------------------------------------------------------------------------

def delete_stored_file(file_path: str, resource_type: str = "raw", is_private: bool = True):
    """Delete a file from Cloudinary (if public_id) or local filesystem (if exists)."""
    if not file_path:
        return
    if is_cloudinary_id(file_path):
        try:
            configure_cloudinary()
            import cloudinary.uploader
            kwargs = {"resource_type": resource_type}
            if is_private:
                kwargs["type"] = "private"
            cloudinary.uploader.destroy(file_path, **kwargs)
            logger.info(f"Destroyed Cloudinary asset: {file_path}")
        except Exception as e:
            logger.warning(f"Error destroying Cloudinary asset {file_path}: {e}")
    else:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted local file: {file_path}")
        except Exception as e:
            logger.warning(f"Error deleting local file {file_path}: {e}")
