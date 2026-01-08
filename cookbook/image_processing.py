from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image


def split_to_aspect_ratio(
    image_path: Path,
    output_dir: Path,
    target_ratio: float,
    margin_ratio: float,
) -> list[Path]:
    """Split or copy an image to meet a target aspect ratio.

    Args:
        image_path: Path to the input image.
        output_dir: Directory to write split images.
        target_ratio: Desired width/height ratio.
        margin_ratio: Overlap ratio between splits.

    Returns:
        List of paths to generated images.
    """

    # Load image metadata to determine split strategy.
    output_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path) as image:
        width, height = image.size
        current_ratio = width / height

        if abs(current_ratio - target_ratio) < 0.01:
            output_path = output_dir / image_path.name
            image.save(output_path)
            return [output_path]

        if current_ratio > target_ratio:
            return _split_wide(image, image_path, output_dir, target_ratio, margin_ratio)
        return _split_tall(image, image_path, output_dir, target_ratio, margin_ratio)


def _split_tall(
    image: Image.Image,
    image_path: Path,
    output_dir: Path,
    target_ratio: float,
    margin_ratio: float,
) -> list[Path]:
    """Split a tall image into overlapping crops.

    Args:
        image: Loaded PIL image.
        image_path: Source image path.
        output_dir: Directory to write split images.
        target_ratio: Desired width/height ratio.
        margin_ratio: Overlap ratio between splits.

    Returns:
        List of paths to generated images.
    """

    # Slide a crop window vertically to create splits.
    width, height = image.size
    crop_height = int(width / target_ratio)
    step = int(crop_height * (1 - margin_ratio))
    if step <= 0:
        step = crop_height
    crops = []
    index = 0
    for top in range(0, height - crop_height + 1, step):
        crop = image.crop((0, top, width, top + crop_height))
        output_path = output_dir / f"{image_path.stem}_part{index}.jpg"
        crop.save(output_path)
        crops.append(output_path)
        index += 1
    return crops


def _split_wide(
    image: Image.Image,
    image_path: Path,
    output_dir: Path,
    target_ratio: float,
    margin_ratio: float,
) -> list[Path]:
    """Split a wide image into overlapping crops.

    Args:
        image: Loaded PIL image.
        image_path: Source image path.
        output_dir: Directory to write split images.
        target_ratio: Desired width/height ratio.
        margin_ratio: Overlap ratio between splits.

    Returns:
        List of paths to generated images.
    """

    # Slide a crop window horizontally to create splits.
    width, height = image.size
    crop_width = int(height * target_ratio)
    step = int(crop_width * (1 - margin_ratio))
    if step <= 0:
        step = crop_width
    crops = []
    index = 0
    for left in range(0, width - crop_width + 1, step):
        crop = image.crop((left, 0, left + crop_width, height))
        output_path = output_dir / f"{image_path.stem}_part{index}.jpg"
        crop.save(output_path)
        crops.append(output_path)
        index += 1
    return crops


def split_images(
    image_paths: Iterable[Path],
    output_dir: Path,
    target_ratio: float,
    margin_ratio: float,
) -> list[Path]:
    """Split multiple images to match the target ratio.

    Args:
        image_paths: Iterable of image paths.
        output_dir: Directory to write split images.
        target_ratio: Desired width/height ratio.
        margin_ratio: Overlap ratio between splits.

    Returns:
        List of all split image paths.
    """

    # Apply ratio splits to each image in sequence.
    results = []
    for image_path in image_paths:
        results.extend(
            split_to_aspect_ratio(image_path, output_dir, target_ratio, margin_ratio)
        )
    return results
