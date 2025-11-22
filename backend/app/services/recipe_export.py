"""
Recipe export service for generating recipes in various formats.
"""

import json
from typing import Any

from app.models.recipe import Recipe
from app.utils.recipe_format import convert_to_schema_org


class RecipeExporter:
    """Service for exporting recipes to various formats."""

    def export_json(self, recipe: Recipe) -> str:
        """
        Export recipe as JSON in Schema.org Recipe format.

        Args:
            recipe: Recipe model instance

        Returns:
            JSON string representation
        """
        schema_recipe = convert_to_schema_org(recipe)
        return json.dumps(schema_recipe, indent=2)

    def export_markdown(self, recipe: Recipe) -> str:
        """
        Export recipe as Markdown.

        Args:
            recipe: Recipe model instance

        Returns:
            Markdown formatted string
        """
        schema_recipe = convert_to_schema_org(recipe)
        lines = [f"# {schema_recipe['name']}\n"]

        if schema_recipe.get("description"):
            lines.append(f"{schema_recipe['description']}\n")

        # Add metadata
        metadata = self._format_metadata(schema_recipe, markdown=True)
        if metadata:
            lines.append("")
            lines.extend(metadata)

        # Ingredients
        if schema_recipe.get("recipeIngredient"):
            lines.append("\n## Ingredients")
            for ingredient in schema_recipe["recipeIngredient"]:
                lines.append(f"- {ingredient}")

        # Equipment
        equipment = schema_recipe.get("equipment")
        if equipment:
            lines.append("\n## Equipment")
            if isinstance(equipment, list):
                for item in equipment:
                    lines.append(f"- {item}")
            elif isinstance(equipment, str):
                lines.append(f"- {equipment}")

        # Instructions
        instructions = schema_recipe.get("recipeInstructions")
        if instructions:
            lines.append("\n## Instructions")
            self._format_instructions(lines, instructions, markdown=True)

        # Notes
        if schema_recipe.get("notes"):
            lines.append("\n## Notes\n")
            lines.append(schema_recipe["notes"])

        # Nutrition
        nutrition = schema_recipe.get("nutrition")
        if nutrition and isinstance(nutrition, dict):
            lines.append("\n## Nutrition Information\n")
            for key, value in nutrition.items():
                if value:
                    label = "".join([" " + c if c.isupper() else c for c in key]).strip().title()
                    lines.append(f"- **{label}:** {value}")

        # Images
        images = schema_recipe.get("image")
        if images:
            lines.append("\n")
            self._format_images(lines, images, markdown=True)

        return "\n".join(lines)

    def export_text(self, recipe: Recipe) -> str:
        """
        Export recipe as plain text.

        Args:
            recipe: Recipe model instance

        Returns:
            Plain text formatted string
        """
        schema_recipe = convert_to_schema_org(recipe)
        lines = [
            f"{schema_recipe['name'].upper()}",
            "=" * len(schema_recipe["name"]),
        ]

        if schema_recipe.get("description"):
            lines.append(f"\n{schema_recipe['description']}\n")

        # Add metadata
        metadata = self._format_metadata(schema_recipe, markdown=False)
        if metadata:
            lines.extend(metadata)

        # Ingredients
        if schema_recipe.get("recipeIngredient"):
            lines.append("\nINGREDIENTS:")
            for ingredient in schema_recipe["recipeIngredient"]:
                lines.append(f"  - {ingredient}")

        # Equipment
        equipment = schema_recipe.get("equipment")
        if equipment:
            lines.append("\nEQUIPMENT:")
            if isinstance(equipment, list):
                for item in equipment:
                    lines.append(f"  - {item}")
            elif isinstance(equipment, str):
                lines.append(f"  - {equipment}")

        # Instructions
        instructions = schema_recipe.get("recipeInstructions")
        if instructions:
            lines.append("\nINSTRUCTIONS:")
            self._format_instructions(lines, instructions, markdown=False)

        # Notes
        if schema_recipe.get("notes"):
            lines.append("\nNOTES:")
            lines.append(f"  {schema_recipe['notes']}")

        # Nutrition
        nutrition = schema_recipe.get("nutrition")
        if nutrition and isinstance(nutrition, dict):
            lines.append("\nNUTRITION INFORMATION:")
            for key, value in nutrition.items():
                if value:
                    label = "".join([" " + c if c.isupper() else c for c in key]).strip().title()
                    lines.append(f"  {label}: {value}")

        return "\n".join(lines)

    def export_pdf(self, recipe: Recipe) -> bytes:
        """
        Export recipe as PDF.

        Args:
            recipe: Recipe model instance

        Returns:
            PDF file as bytes
        """
        # Lazy import to avoid requiring WeasyPrint dependencies when not using PDF export
        from app.utils.pdf_export import generate_recipe_pdf

        return generate_recipe_pdf(recipe)

    def _format_metadata(self, schema_recipe: dict[str, Any], markdown: bool = False) -> list[str]:
        """
        Format recipe metadata (yield, times, category, etc.).

        Args:
            schema_recipe: Recipe in Schema.org format
            markdown: Whether to use markdown formatting (bold labels)

        Returns:
            List of formatted metadata lines
        """
        metadata_items = []

        fields = [
            ("recipeYield", "Yield"),
            ("prepTime", "Prep Time"),
            ("cookTime", "Cook Time"),
            ("totalTime", "Total Time"),
        ]

        for field, label in fields:
            if schema_recipe.get(field):
                if markdown:
                    metadata_items.append(f"**{label}:** {schema_recipe[field]}")
                else:
                    metadata_items.append(f"{label}: {schema_recipe[field]}")

        # Category
        if schema_recipe.get("recipeCategory"):
            categories = schema_recipe["recipeCategory"]
            category_str = (
                ", ".join(categories) if isinstance(categories, list) else str(categories)
            )
            if markdown:
                metadata_items.append(f"**Category:** {category_str}")
            else:
                metadata_items.append(f"Category: {category_str}")

        # Cuisine
        if schema_recipe.get("recipeCuisine"):
            cuisines = schema_recipe["recipeCuisine"]
            cuisine_str = ", ".join(cuisines) if isinstance(cuisines, list) else str(cuisines)
            if markdown:
                metadata_items.append(f"**Cuisine:** {cuisine_str}")
            else:
                metadata_items.append(f"Cuisine: {cuisine_str}")

        # Keywords
        if schema_recipe.get("keywords"):
            if markdown:
                metadata_items.append(f"**Keywords:** {schema_recipe['keywords']}")
            else:
                metadata_items.append(f"Keywords: {schema_recipe['keywords']}")

        # Source URL
        if schema_recipe.get("url"):
            if markdown:
                metadata_items.append(f"**Source:** {schema_recipe['url']}")
            else:
                metadata_items.append(f"Source: {schema_recipe['url']}")

        return metadata_items

    def _format_instructions(
        self, lines: list[str], instructions: Any, markdown: bool = False
    ) -> None:
        """
        Format recipe instructions.

        Args:
            lines: List to append formatted instructions to
            instructions: Instructions data (list or string)
            markdown: Whether to use markdown formatting
        """
        if isinstance(instructions, list):
            for i, step in enumerate(instructions, 1):
                step_text = step.get("text", str(step)) if isinstance(step, dict) else str(step)
                if markdown:
                    lines.append(f"{i}. {step_text}")
                else:
                    lines.append(f"  {i}. {step_text}")
        elif isinstance(instructions, str):
            if markdown:
                lines.append(instructions)
            else:
                lines.append(f"  {instructions}")

    def _format_images(self, lines: list[str], images: Any, markdown: bool = False) -> None:
        """
        Format recipe images for markdown export.

        Args:
            lines: List to append formatted images to
            images: Images data (list or string)
            markdown: Whether to use markdown formatting
        """
        if not markdown:
            return  # Plain text doesn't support images

        if isinstance(images, list) and images:
            for idx, img in enumerate(images, 1):
                if isinstance(img, dict):
                    if img.get("data"):
                        # Image has base64 data
                        mime_type = img.get("mimeType", "image/jpeg")
                        lines.append(
                            f"![Recipe Image {idx}](data:{mime_type};base64,{img['data']})"
                        )
                    elif img.get("url"):
                        # Image has URL
                        lines.append(f"![Recipe Image {idx}]({img['url']})")
        elif isinstance(images, str):
            # Single image URL or base64
            lines.append(f"![Recipe Image](data:image/jpeg;base64,{images})")
