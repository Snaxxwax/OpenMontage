from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CHANNEL_PUBLIC = ROOT / "channels" / "modern-archivist" / "remotion" / "public"
COMPOSER_PUBLIC = ROOT / "remotion-composer" / "public" / "modern-archivist"


def _alpha_stats(path: Path) -> tuple[float, tuple[int, int, int, int] | None]:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    hist = alpha.histogram()
    transparent_ratio = sum(hist[:10]) / (image.width * image.height)
    return transparent_ratio, alpha.getbbox()


def test_public_archivist_body_has_hard_alpha_not_white_square() -> None:
    for root in [CHANNEL_PUBLIC, COMPOSER_PUBLIC]:
        transparent_ratio, bbox = _alpha_stats(root / "archivist-body.png")
        assert transparent_ratio > 0.25
        assert bbox is not None
        assert bbox != (0, 0, 1254, 1254)


def test_public_archivist_mug_has_hard_alpha_not_white_square() -> None:
    for root in [CHANNEL_PUBLIC, COMPOSER_PUBLIC]:
        transparent_ratio, bbox = _alpha_stats(root / "archivist-mug.png")
        assert transparent_ratio > 0.45
        assert bbox is not None
        assert bbox != (0, 0, 1254, 1254)
