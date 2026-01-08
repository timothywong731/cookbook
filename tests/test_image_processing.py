from pathlib import Path

from PIL import Image

from cookbook.image_processing import split_images, split_to_aspect_ratio


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


def test_split_images_multiple(tmp_path: Path) -> None:
    """Test splitting multiple images using split_images."""
    image1 = tmp_path / "img1.jpg"
    image2 = tmp_path / "img2.jpg"
    _make_image(image1, (100, 200))
    _make_image(image2, (200, 100))

    output_dir = tmp_path / "multi_splits"
    results = split_images([image1, image2], output_dir, 1.0, 0.5)

    # image1 (100, 200) with ratio 1.0 -> 100x100 crops.
    # crop_height = 100. step = 100 * (1 - 0.5) = 50.
    # range(0, 200 - 100 + 1, 50) -> 0, 50, 100. (3 crops)
    # image2 (200, 100) with ratio 1.0 -> 100x100 crops.
    # crop_width = 100. step = 100 * (1 - 0.5) = 50.
    # range(0, 200 - 100 + 1, 50) -> 0, 50, 100. (3 crops)
    # Total 6 crops.
    assert len(results) == 6


def test_split_tall_edge_cases(tmp_path: Path) -> None:
    """Test edge cases for _split_tall."""
    output_dir = tmp_path / "edge_tall"

    # Case 1: multiple crops with overlapping margin
    # width=100, height=100, target_ratio=1.5 -> crop_height = 66.
    # margin_ratio=0.5 -> step = 33.
    # range(0, 100-66+1, 33) -> range(0, 35, 33) -> 0, 33.
    image_path = tmp_path / "edge1.jpg"
    _make_image(image_path, (100, 100))
    results = split_to_aspect_ratio(image_path, output_dir, 1.5, 0.5)
    assert len(results) == 2

    # Case 2: step <= 0 (via margin_ratio >= 1.0)
    # width=100, height=200, target_ratio=1.0 -> crop_height = 100.
    # margin_ratio=1.0 -> step = 0. Should be set to crop_height=100.
    image_path = tmp_path / "edge2.jpg"
    _make_image(image_path, (100, 200))
    results = split_to_aspect_ratio(image_path, output_dir, 1.0, 1.0)
    assert len(results) == 2  # range(0, 200-100+1, 100) -> 0, 100


def test_split_wide_edge_cases(tmp_path: Path) -> None:
    """Test edge cases for _split_wide."""
    output_dir = tmp_path / "edge_wide"

    # Case 1: multiple crops with overlapping margin
    # width=100, height=100, target_ratio=0.5 -> crop_width = 50.
    # margin_ratio=0.1 -> step = 45.
    # range(0, 100-50+1, 45) -> range(0, 51, 45) -> 0, 45.
    image_path = tmp_path / "wide1.jpg"
    _make_image(image_path, (100, 100))
    results = split_to_aspect_ratio(image_path, output_dir, 0.5, 0.1)
    assert len(results) == 2

    # Case 2: step <= 0
    # width=200, height=100, target_ratio=1.0 -> crop_width = 100.
    # margin_ratio=1.0 -> step = 0. Should be set to crop_width=100.
    image_path = tmp_path / "wide2.jpg"
    _make_image(image_path, (200, 100))
    results = split_to_aspect_ratio(image_path, output_dir, 1.0, 1.1)
    assert len(results) == 2
