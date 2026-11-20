import io
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
FORMAT_EXT = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}


def process_profile_image(uploaded_file, max_bytes=None, max_size=(1024, 1024)):
    """Validate and normalize an uploaded profile image.

    - enforces max size
    - verifies it's a real image
    - strips metadata/EXIF by re-encoding pixels
    - applies EXIF orientation
    - resizes to fit within max_size
    Returns (filename, ContentFile).
    """
    if uploaded_file is None:
        return None

    max_bytes = max_bytes or getattr(settings, 'PROFILE_IMAGE_MAX_BYTES', 5 * 1024 * 1024)
    size = getattr(uploaded_file, 'size', None)
    if size is not None and size > max_bytes:
        raise ValidationError('Bilddatei ist zu groß.')

    pos = uploaded_file.tell() if hasattr(uploaded_file, 'tell') else None
    try:
        if hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(0)
        data = uploaded_file.read()
    finally:
        if pos is not None:
            try:
                uploaded_file.seek(pos)
            except Exception:
                pass

    if not data:
        raise ValidationError('Ungültige Bilddatei.')
    if len(data) > max_bytes:
        raise ValidationError('Bilddatei ist zu groß.')

    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
    except Exception:
        raise ValidationError('Bitte eine gültige Bilddatei hochladen.')

    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)
        fmt = (img.format or 'JPEG').upper()
        if fmt == 'JPG':
            fmt = 'JPEG'
        if fmt not in ALLOWED_FORMATS:
            fmt = 'JPEG'

        if fmt == 'JPEG':
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                bg = Image.new('RGB', img.size, (255, 255, 255))
                rgba = img.convert('RGBA')
                bg.paste(rgba, mask=rgba.split()[-1])
                img = bg
            else:
                img = img.convert('RGB')
        elif fmt == 'PNG':
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA')
        else:  # WEBP
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA' if 'transparency' in img.info else 'RGB')

        img.thumbnail(max_size, Image.LANCZOS)
        out = io.BytesIO()
        save_kwargs = {}
        if fmt == 'JPEG':
            save_kwargs.update({'quality': 85, 'optimize': True, 'progressive': True})
        elif fmt == 'PNG':
            save_kwargs.update({'optimize': True})
        else:
            save_kwargs.update({'quality': 85, 'method': 6})
        img.save(out, format=fmt, **save_kwargs)
        content = out.getvalue()
    except ValidationError:
        raise
    except Exception:
        raise ValidationError('Bild konnte nicht verarbeitet werden.')

    if len(content) > max_bytes:
        raise ValidationError('Bilddatei ist nach Verarbeitung zu groß.')

    ext = FORMAT_EXT.get(fmt, 'jpg')
    base = os.path.splitext(os.path.basename(getattr(uploaded_file, 'name', 'upload') or 'upload'))[0]
    base = ''.join(c for c in base if c.isalnum() or c in ('-', '_'))[:40] or 'photo'
    filename = f"{base}.{ext}"
    return filename, ContentFile(content, name=filename)
