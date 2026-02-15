"""
iTaK Media Pipeline - Unified inbound/outbound media handling.

Normalizes image, audio, video, and document attachments across
all adapters (Discord, Telegram, Slack, Dashboard).

Gameplan §26.7 - "Media Pipeline"
"""

import asyncio
import hashlib
import json
import logging
import mimetypes
import os
import shutil
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger("itak.media")


class MediaType(str, Enum):
    """Supported media categories."""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


# File extension → media type mapping
EXTENSION_MAP = {
    # Images
    ".png": MediaType.IMAGE, ".jpg": MediaType.IMAGE,
    ".jpeg": MediaType.IMAGE, ".gif": MediaType.IMAGE,
    ".webp": MediaType.IMAGE, ".bmp": MediaType.IMAGE,
    ".svg": MediaType.IMAGE, ".ico": MediaType.IMAGE,
    # Audio
    ".mp3": MediaType.AUDIO, ".ogg": MediaType.AUDIO,
    ".wav": MediaType.AUDIO, ".m4a": MediaType.AUDIO,
    ".flac": MediaType.AUDIO, ".aac": MediaType.AUDIO,
    # Video
    ".mp4": MediaType.VIDEO, ".webm": MediaType.VIDEO,
    ".mov": MediaType.VIDEO, ".avi": MediaType.VIDEO,
    ".mkv": MediaType.VIDEO,
    # Documents
    ".pdf": MediaType.DOCUMENT, ".txt": MediaType.DOCUMENT,
    ".md": MediaType.DOCUMENT, ".csv": MediaType.DOCUMENT,
    ".json": MediaType.DOCUMENT, ".xml": MediaType.DOCUMENT,
    ".py": MediaType.DOCUMENT, ".js": MediaType.DOCUMENT,
    ".ts": MediaType.DOCUMENT, ".html": MediaType.DOCUMENT,
    ".css": MediaType.DOCUMENT, ".yaml": MediaType.DOCUMENT,
    ".yml": MediaType.DOCUMENT, ".toml": MediaType.DOCUMENT,
    ".sh": MediaType.DOCUMENT, ".sql": MediaType.DOCUMENT,
    ".log": MediaType.DOCUMENT, ".ini": MediaType.DOCUMENT,
    ".env": MediaType.DOCUMENT, ".dockerfile": MediaType.DOCUMENT,
    ".rs": MediaType.DOCUMENT, ".go": MediaType.DOCUMENT,
    ".java": MediaType.DOCUMENT, ".c": MediaType.DOCUMENT,
    ".cpp": MediaType.DOCUMENT, ".h": MediaType.DOCUMENT,
    ".docx": MediaType.DOCUMENT, ".xlsx": MediaType.DOCUMENT,
}

# Per-adapter size limits (bytes)
SIZE_LIMITS = {
    "discord": 25 * 1024 * 1024,     # 25MB
    "telegram": 50 * 1024 * 1024,    # 50MB
    "slack": 1 * 1024 * 1024 * 1024, # 1GB
    "dashboard": 0,                   # Unlimited
}


@dataclass
class MediaItem:
    """A processed media item."""
    id: str                          # Hash-based unique ID
    type: MediaType
    path: str                        # Local file path
    original_filename: str
    size_bytes: int = 0
    mime_type: str = ""
    extracted_content: str = ""      # Text content / description / transcript
    room_id: str = ""
    timestamp: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class Attachment:
    """An inbound attachment from any adapter."""
    filename: str
    url: str = ""                    # Remote URL to download
    data: bytes = b""                # Raw bytes (if already downloaded)
    size_bytes: int = 0
    content_type: str = ""


class MediaPipeline:
    """
    Unified inbound/outbound media handling.

    Inbound (User → Agent):
      - Download attachments to data/rooms/{room}/media/
      - Classify: image / audio / document / video
      - Extract content: OCR, transcription, text parsing

    Outbound (Agent → User):
      - Normalize file sending per adapter
      - Size limit enforcement with fallback to download links

    Usage:
        pipeline = MediaPipeline(agent)
        item = await pipeline.process_inbound(attachment, room_id="discord_dm_123")
        # item.extracted_content has the text
    """

    def __init__(self, agent=None, config: dict | None = None):
        self.agent = agent
        self.config = config or {}
        self.base_dir = Path(self.config.get("media_dir", "data/rooms"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self._stats = {
            "inbound_processed": 0,
            "outbound_sent": 0,
            "total_bytes_in": 0,
            "total_bytes_out": 0,
            "errors": 0,
        }

        logger.info("Media Pipeline initialized")

    # ── Backward-compatible helper API ───────────────────────

    async def process_image(self, path: str) -> str:
        return await self._extract_image(Path(path))

    async def process_audio(self, path: str) -> str:
        return await self._extract_audio(Path(path))

    async def classify_file(self, path: str) -> str:
        return self.classify(path).value

    # ── Classification ─────────────────────────────────────────

    def classify(self, path: str | Path) -> MediaType:
        """Classify a file into a media type by extension."""
        ext = Path(path).suffix.lower()
        return EXTENSION_MAP.get(ext, MediaType.UNKNOWN)

    def get_mime_type(self, path: str | Path) -> str:
        """Get MIME type for a file."""
        mime, _ = mimetypes.guess_type(str(path))
        return mime or "application/octet-stream"

    # ── Inbound Processing ─────────────────────────────────────

    async def process_inbound(self, attachment: Attachment,
                               room_id: str = "default") -> MediaItem:
        """
        Process an inbound attachment.

        Downloads, classifies, extracts content, and stores locally.
        """
        # Ensure media directory exists
        media_dir = self.base_dir / room_id / "media"
        media_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        timestamp = time.time()
        file_ext = Path(attachment.filename).suffix.lower() or ".bin"
        content_hash = hashlib.md5(
            (attachment.filename + str(timestamp)).encode()
        ).hexdigest()[:8]
        local_filename = f"{int(timestamp)}_{content_hash}{file_ext}"
        local_path = media_dir / local_filename

        # Download or save
        if attachment.data:
            local_path.write_bytes(attachment.data)
        elif attachment.url:
            await self._download_file(attachment.url, local_path)
        else:
            raise ValueError("Attachment has no data or URL")

        # Get file info
        size = local_path.stat().st_size if local_path.exists() else 0
        media_type = self.classify(local_path)
        mime = self.get_mime_type(local_path)

        # Extract content based on type
        extracted = ""
        try:
            extracted = await self._extract_content(local_path, media_type)
        except Exception as e:
            logger.warning(f"Content extraction failed for {attachment.filename}: {e}")

        # Create MediaItem
        item = MediaItem(
            id=content_hash,
            type=media_type,
            path=str(local_path),
            original_filename=attachment.filename,
            size_bytes=size,
            mime_type=mime,
            extracted_content=extracted,
            room_id=room_id,
            timestamp=timestamp,
        )

        # Update manifest
        await self._update_manifest(media_dir, item)

        self._stats["inbound_processed"] += 1
        self._stats["total_bytes_in"] += size

        logger.info(
            f"Media inbound: {attachment.filename} → {media_type.value} "
            f"({size} bytes, extracted {len(extracted)} chars)"
        )

        return item

    async def _download_file(self, url: str, dest: Path):
        """Download a file from URL."""
        import urllib.request

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: urllib.request.urlretrieve(url, str(dest))
        )

    async def _extract_content(self, path: Path, media_type: MediaType) -> str:
        """Extract text content from a media file."""

        if media_type == MediaType.DOCUMENT:
            return await self._extract_document(path)

        elif media_type == MediaType.IMAGE:
            return await self._extract_image(path)

        elif media_type == MediaType.AUDIO:
            return await self._extract_audio(path)

        return ""  # Videos: no extraction by default

    async def _extract_document(self, path: Path) -> str:
        """Extract text from document files."""
        ext = path.suffix.lower()

        # Plain text files
        text_extensions = {
            ".txt", ".md", ".csv", ".json", ".xml", ".py", ".js", ".ts",
            ".html", ".css", ".yaml", ".yml", ".toml", ".sh", ".sql",
            ".log", ".ini", ".env", ".rs", ".go", ".java", ".c", ".cpp",
            ".h",
        }

        if ext in text_extensions:
            try:
                return path.read_text(encoding="utf-8", errors="replace")[:10000]
            except Exception:
                return path.read_text(encoding="latin-1", errors="replace")[:10000]

        elif ext == ".pdf":
            return await self._extract_pdf(path)

        return f"[Document: {path.name}, {path.stat().st_size} bytes]"

    async def _extract_pdf(self, path: Path) -> str:
        """Extract text from PDF - tries multiple methods."""
        # Try PyMuPDF (fitz) first
        try:
            import fitz
            doc = fitz.open(str(path))
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text[:10000]
        except ImportError:
            pass

        # Try pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text[:10000]
        except ImportError:
            pass

        return f"[PDF: {path.name}, install pymupdf or pypdf for extraction]"

    async def _extract_image(self, path: Path) -> str:
        """Describe an image using the agent's vision model."""
        # If agent has a vision-capable model, use it
        try:
            if hasattr(self.agent, 'model_router') and self.agent.model_router:
                import base64
                image_data = base64.b64encode(path.read_bytes()).decode()
                mime = self.get_mime_type(path)

                result = await self.agent.model_router.chat(
                    [{"role": "user", "content": [
                        {"type": "text", "text": "Describe this image concisely."},
                        {"type": "image_url", "image_url": {
                            "url": f"data:{mime};base64,{image_data}"
                        }},
                    ]}],
                    purpose="utility"
                )
                return result
        except Exception as e:
            logger.debug(f"Vision extraction failed: {e}")

        return f"[Image: {path.name}, {path.stat().st_size} bytes]"

    async def _extract_audio(self, path: Path) -> str:
        """Transcribe audio using Whisper."""
        # Try local Whisper
        try:
            import whisper
            model = whisper.load_model("base")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: model.transcribe(str(path))
            )
            return result.get("text", "")
        except ImportError:
            pass

        return f"[Audio: {path.name}, install openai-whisper for transcription]"

    # ── Outbound ───────────────────────────────────────────────

    async def send_outbound(self, path: str | Path, room_id: str,
                            adapter_name: str = "dashboard") -> dict:
        """
        Send a file through the appropriate adapter.

        Returns:
            {"status": "sent", "method": "direct|link", "url": "..."}
        """
        path = Path(path)
        if not path.exists():
            return {"status": "error", "error": f"File not found: {path}"}

        size = path.stat().st_size
        size_limit = SIZE_LIMITS.get(adapter_name, 0)

        # Check size limits
        if size_limit > 0 and size > size_limit:
            # File too large - provide download link instead
            self._stats["outbound_sent"] += 1
            self._stats["total_bytes_out"] += size
            return {
                "status": "sent",
                "method": "link",
                "message": (
                    f"File `{path.name}` ({size // 1024}KB) exceeds "
                    f"{adapter_name} limit. Saved locally: {path}"
                ),
            }

        self._stats["outbound_sent"] += 1
        self._stats["total_bytes_out"] += size

        return {
            "status": "sent",
            "method": "direct",
            "path": str(path),
            "filename": path.name,
            "size_bytes": size,
            "mime_type": self.get_mime_type(path),
        }

    # ── Manifest ───────────────────────────────────────────────

    async def _update_manifest(self, media_dir: Path, item: MediaItem):
        """Update the room's media manifest."""
        manifest_path = media_dir / "manifest.json"

        manifest = []
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                manifest = []

        manifest.append({
            "id": item.id,
            "type": item.type.value,
            "filename": item.original_filename,
            "path": item.path,
            "size_bytes": item.size_bytes,
            "mime_type": item.mime_type,
            "timestamp": item.timestamp,
            "has_content": bool(item.extracted_content),
        })

        manifest_path.write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

    # ── Status ─────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get media pipeline statistics."""
        return {
            **self._stats,
            "media_dir": str(self.base_dir),
        }
