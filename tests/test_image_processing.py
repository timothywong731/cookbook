from pathlib import Path

from PIL import Image

from cookbook.image_processing import split_to_aspect_ratio


def _make_image(path: Path, size: tuple[int, int]) -> None:
    """Create a blank RGB image for testing.

    Args:
        path: Destination file path.
        size: Image size (width, height).
    """

    # Generate a simple in-memory image for tests.
    image = Image.new("RGB", size, color=(255, 255, 255))
    image.save(path)


def test_split_tall_image(tmp_path: Path) -> None:
    """Split a tall image into multiple crops."""

    # Create a tall image to force vertical splits.
    image_path = tmp_path / "tall.jpg"
    _make_image(image_path, (100, 300))

    output_dir = tmp_path / "splits"
    results = split_to_aspect_ratio(image_path, output_dir, 1.0, 0.1)

    assert len(results) == 3
    for result in results:
        # Verify each crop meets the target size.
        with Image.open(result) as crop:
            assert crop.size == (100, 100)


def test_split_wide_image(tmp_path: Path) -> None:
    """Split a wide image into multiple crops."""

    # Create a wide image to force horizontal splits.
    image_path = tmp_path / "wide.jpg"
    _make_image(image_path, (300, 100))

    output_dir = tmp_path / "splits"
    results = split_to_aspect_ratio(image_path, output_dir, 1.0, 0.1)

    assert len(results) == 3
    for result in results:
        # Verify each crop meets the target size.
        with Image.open(result) as crop:
            assert crop.size == (100, 100)


def test_split_matching_ratio(tmp_path: Path) -> None:
    """Copy an image that already matches the aspect ratio."""

    # Create an image with the desired aspect ratio.
    image_path = tmp_path / "ratio.jpg"
    _make_image(image_path, (80, 100))

    output_dir = tmp_path / "splits"
    results = split_to_aspect_ratio(image_path, output_dir, 0.8, 0.1)

    # Ensure a single output file is produced.
    assert len(results) == 1
