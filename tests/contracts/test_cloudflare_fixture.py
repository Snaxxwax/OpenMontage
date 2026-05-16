from __future__ import annotations

import json
import unittest
from pathlib import Path

from PIL import Image

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "cloudflare-chokepoint-test"
MANIFEST_PATH = FIXTURE_ROOT / "source_card_manifest.json"
SC02_CARD_PATH = FIXTURE_ROOT / "assets" / "composed" / "SC-02-card.png"


def _sc02(manifest: dict) -> dict:
    for card in manifest["cards"]:
        if card["card_id"] == "SC-02":
            return card
    raise KeyError("SC-02 not found in fixture manifest")


class CloudflareFixtureTests(unittest.TestCase):

    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.card = _sc02(self.manifest)

    def test_sc02_crop_height_is_322(self) -> None:
        self.assertEqual(self.card["crop"]["h"], 322)

    def test_sc02_bottom_margin_formula(self) -> None:
        crop = self.card["crop"]
        canvas = self.card["canvas"]
        computed = canvas["w"] - canvas["top_margin"] - crop["h"]
        # canvas.w is 752, canvas.h is 422 — use canvas.h
        computed = canvas["h"] - canvas["top_margin"] - crop["h"]
        self.assertEqual(computed, 90)
        self.assertGreaterEqual(computed, canvas["bottom_safe_margin_px"])

    def test_sc02_card_has_descender_pixels(self) -> None:
        img = Image.open(SC02_CARD_PATH).convert("RGB")
        w = img.width
        # rows 315-332 were previously clipped by the h=315 bug; h=322 fix captures them
        non_white = sum(
            1
            for row in range(315, 333)
            for col in range(w)
            if any(c < 240 for c in img.getpixel((col, row)))
        )
        self.assertGreater(non_white, 0, "No descender pixels found in rows 315-332 — crop fix may have reverted")

    def test_sc02_card_bottom_margin_is_clean(self) -> None:
        img = Image.open(SC02_CARD_PATH).convert("RGB")
        w, h = img.size
        margin_start = 332  # canvas.top_margin(10) + crop.h(322)
        dirty = sum(
            1
            for row in range(margin_start, h)
            for col in range(w)
            if any(c < 240 for c in img.getpixel((col, row)))
        )
        self.assertEqual(dirty, 0, f"{dirty} non-white pixels found in bottom safe margin rows {margin_start}-{h}")


if __name__ == "__main__":
    unittest.main()
