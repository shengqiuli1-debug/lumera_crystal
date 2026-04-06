from __future__ import annotations

from io import BytesIO
from tempfile import NamedTemporaryFile

from PIL import Image, ImageSequence

MAX_GIF_FRAMES = 300


def trim_gif(content: bytes, max_duration_seconds: int) -> tuple[bytes, float]:
    with Image.open(BytesIO(content)) as image:
        frames = []
        durations = []
        total_ms = 0
        max_ms = max_duration_seconds * 1000

        for idx, frame in enumerate(ImageSequence.Iterator(image)):
            if idx >= MAX_GIF_FRAMES:
                break
            frame_duration = int(frame.info.get("duration", 100))
            if total_ms + frame_duration > max_ms:
                remaining = max(0, max_ms - total_ms)
                if remaining > 0:
                    durations.append(remaining)
                    frames.append(frame.convert("RGBA"))
                    total_ms += remaining
                break
            durations.append(frame_duration)
            frames.append(frame.convert("RGBA"))
            total_ms += frame_duration

        if not frames:
            raise ValueError("Invalid GIF content")

        if total_ms <= max_ms and len(frames) == getattr(image, "n_frames", len(frames)):
            return content, total_ms / 1000

        output = BytesIO()
        first, rest = frames[0], frames[1:]
        first.save(
            output,
            format="GIF",
            save_all=True,
            append_images=rest,
            duration=durations,
            loop=0,
            optimize=False,
        )
        return output.getvalue(), total_ms / 1000


def trim_video(content: bytes, mime_type: str, max_duration_seconds: int) -> tuple[bytes, float, str]:
    try:
        from moviepy.editor import VideoFileClip
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("moviepy is required for video processing") from exc

    suffix_map = {
        "video/mp4": ".mp4",
        "video/webm": ".webm",
        "video/quicktime": ".mov",
    }
    suffix = suffix_map.get(mime_type, ".mp4")

    with NamedTemporaryFile(suffix=suffix, delete=True) as src, NamedTemporaryFile(suffix=".mp4", delete=True) as dst:
        src.write(content)
        src.flush()

        with VideoFileClip(src.name) as clip:
            duration = float(clip.duration or 0)
            if duration <= 0:
                raise ValueError("Invalid video duration")
            if duration <= max_duration_seconds:
                return content, duration, mime_type

            trimmed = clip.subclip(0, max_duration_seconds)
            trimmed.write_videofile(
                dst.name,
                codec="libx264",
                audio_codec="aac",
                preset="ultrafast",
                logger=None,
                verbose=False,
            )

        dst.seek(0)
        return dst.read(), float(max_duration_seconds), "video/mp4"
