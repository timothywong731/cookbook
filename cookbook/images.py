from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass
class ImagePreprocessor:
    target_aspect_ratio: float
    margin_ratio: float
    output_dir: Path

    def prepare(self, image_path: Path) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with Image.open(image_path) as image:
            width, height = image.size
            current_ratio = width / height
            if abs(current_ratio - self.target_aspect_ratio) < 0.01:
                output_path = self._save(image, image_path.stem, 0)
                return [output_path]
            return self._split_image(image, image_path.stem)

    def _split_image(self, image: Image.Image, stem: str) -> list[Path]:
        width, height = image.size
        target_width = int(height * self.target_aspect_ratio)
        if target_width <= 0:
            raise ValueError("Invalid target width calculated.")

        step = int(target_width * (1 - self.margin_ratio))
        if step <= 0:
            step = target_width

        crops: list[Path] = []
        left = 0
        index = 0
        while left < width:
            right = min(left + target_width, width)
            crop = image.crop((left, 0, right, height))
            crops.append(self._save(crop, stem, index))
            if right == width:
                break
            left += step
            index += 1
        return crops

    def _save(self, image: Image.Image, stem: str, index: int) -> Path:
        output_path = self.output_dir / f"{stem}_{index}.jpg"
        image.convert("RGB").save(output_path, format="JPEG", quality=95)
        return output_path
