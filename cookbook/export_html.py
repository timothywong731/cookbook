from __future__ import annotations

import argparse
import json
from pathlib import Path

from cookbook.models import Recipe
from cookbook.html_renderer import render_recipe_html, write_recipe_html


def export_all(recipes_dir: Path):
    """Convert all structured JSON recipes in a directory to artistic HTML.

    Args:
        recipes_dir: Directory containing .json and illustration files.
    """
    
    json_files = list(recipes_dir.glob("*.json"))
    print(f"Found {len(json_files)} JSON files in {recipes_dir}")
    
    for json_path in json_files:
        print(f"Processing {json_path.name}...")
        
        try:
            # Load the recipe from JSON.
            content = json_path.read_text(encoding="utf-8")
            recipe = Recipe.model_validate_json(content)
            
            # Find the illustration path (expected pattern: {BaseName}_illustration.png)
            illustration_path = json_path.parent / f"{json_path.stem}_illustration.png"
            
            if not illustration_path.exists():
                print(f"  Warning: Illustration not found at {illustration_path.name}. HTML may have broken image.")
            
            html_content = render_recipe_html(recipe, illustration_path)
            html_path = json_path.with_suffix(".html")
            
            write_recipe_html(html_path, html_content)
            print(f"  Generated {html_path.name}")
            
        except Exception as e:
            print(f"  Error processing {json_path.name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Export JSON recipes to artistic HTML.")
    parser.add_argument(
        "--dir",
        default="output/recipes",
        help="Directory containing local recipe JSON files.",
    )
    args = parser.parse_args()
    
    recipes_dir = Path(args.dir)
    if not recipes_dir.exists():
        print(f"Directory not found: {recipes_dir}")
        return
        
    export_all(recipes_dir)


if __name__ == "__main__":
    main()
