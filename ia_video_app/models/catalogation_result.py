def chronological_description(frames: list[dict]) -> str:
    """Construye la descripción cronológica editable de un recurso."""
    lines = []
    for frame in frames:
        timestamp = frame.get("timestamp", "00:00")
        synthesis = str(frame.get("synthesis", "")).strip()
        if synthesis:
            lines.append(f"[{timestamp}] {synthesis}")
    return "\n".join(lines)


def build_video_result(video_id: int, frames: list[dict], status: str = "completed") -> dict:
    """Contrato compartido para revisión, exportación y sincronización MAM."""
    return {
        "video_id": int(video_id),
        "status": status,
        "frames": frames,
        "chronological_description": chronological_description(frames),
    }
