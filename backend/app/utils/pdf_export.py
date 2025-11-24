"""
PDF export utility for recipes and collections using fpdf2.
"""

import html
from typing import TYPE_CHECKING, Any

from fpdf import FPDF

from app.utils.recipe_format import convert_to_schema_org


if TYPE_CHECKING:
    from app.models.recipe import Recipe


# Font constants
FONT_FAMILY = "Helvetica"
FONT_SIZE_TITLE = 20
FONT_SIZE_COVER_TITLE = 32
FONT_SIZE_SECTION_HEADER = 14
FONT_SIZE_BODY = 10
FONT_SIZE_DESCRIPTION = 11
FONT_SIZE_TOC_TITLE = 20
FONT_SIZE_TOC_BODY = 11
FONT_SIZE_FOOTER = 8

# Color constants (RGB)
COLOR_PRIMARY_TEXT = (44, 62, 80)
COLOR_BODY_TEXT = (51, 51, 51)
COLOR_SECONDARY_TEXT = (85, 85, 85)
COLOR_FOOTER_TEXT = (128, 128, 128)
COLOR_BORDER = (224, 224, 224)
COLOR_ACCENT = (52, 152, 219)
COLOR_BACKGROUND = (248, 249, 250)


class RecipePDF(FPDF):
    """Custom PDF class for recipe formatting with Unicode support."""

    def __init__(self):
        """Initialize PDF with Unicode font."""
        super().__init__()
        # Use built-in Unicode font support
        # fpdf2 automatically handles Unicode when you don't restrict to core fonts
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        """Add header to each page (empty for now)."""
        pass

    def footer(self):
        """Add page numbers to footer."""
        self.set_y(-15)
        self.set_font(FONT_FAMILY, "I", FONT_SIZE_FOOTER)
        self.set_text_color(*COLOR_FOOTER_TEXT)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def generate_recipe_pdf(recipe: "Recipe") -> bytes:
    """
    Generate a PDF for a single recipe.

    Args:
        recipe: Recipe model instance

    Returns:
        bytes: PDF file content
    """
    # Convert recipe to schema.org format
    schema_recipe = convert_to_schema_org(recipe)

    # Create PDF
    pdf = RecipePDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Add recipe content
    _add_recipe_to_pdf(pdf, schema_recipe)

    # Return PDF as bytes
    output = pdf.output()
    return bytes(output) if not isinstance(output, bytes) else output


def generate_collection_pdf(
    collection_name: str, collection_description: str, recipes: list["Recipe"]
) -> bytes:
    """
    Generate a PDF for a collection of recipes.

    Args:
        collection_name: Name of the collection
        collection_description: Description of the collection
        recipes: List of Recipe model instances

    Returns:
        bytes: PDF file content
    """
    pdf = RecipePDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Add cover page
    pdf.add_page()
    _add_collection_cover(pdf, collection_name, collection_description)

    # Add table of contents
    if len(recipes) > 1:
        pdf.add_page()
        _add_table_of_contents(pdf, recipes)

    # Add each recipe
    for recipe in recipes:
        pdf.add_page()
        schema_recipe = convert_to_schema_org(recipe)
        _add_recipe_to_pdf(pdf, schema_recipe)

    output = pdf.output()
    return bytes(output) if not isinstance(output, bytes) else output


def _add_collection_cover(pdf: FPDF, name: str, description: str):
    """Add collection cover page."""
    # Center vertically
    pdf.set_y(80)

    # Collection title
    pdf.set_font(FONT_FAMILY, "B", FONT_SIZE_COVER_TITLE)
    pdf.set_text_color(*COLOR_PRIMARY_TEXT)
    pdf.multi_cell(0, 15, _clean_text(name), align="C")

    # Description
    if description:
        pdf.ln(10)
        pdf.set_font(FONT_FAMILY, "", FONT_SIZE_DESCRIPTION)
        pdf.set_text_color(*COLOR_SECONDARY_TEXT)
        pdf.multi_cell(0, 8, _clean_text(description), align="C")


def _add_table_of_contents(pdf: FPDF, recipes: list["Recipe"]):
    """Add table of contents page."""
    pdf.set_font(FONT_FAMILY, "B", FONT_SIZE_TOC_TITLE)
    pdf.set_text_color(*COLOR_PRIMARY_TEXT)
    pdf.cell(0, 12, "Table of Contents", ln=True)
    pdf.ln(5)

    # Draw underline
    pdf.set_draw_color(*COLOR_BORDER)
    pdf.set_line_width(0.5)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 180, pdf.get_y())
    pdf.ln(8)

    # List recipes
    pdf.set_font(FONT_FAMILY, "", FONT_SIZE_TOC_BODY)
    pdf.set_text_color(*COLOR_BODY_TEXT)
    for i, recipe in enumerate(recipes, 1):
        pdf.cell(10, 8, f"{i}.")
        pdf.multi_cell(0, 8, _clean_text(recipe.name))


def _add_recipe_to_pdf(pdf: FPDF, schema_recipe: dict[str, Any]):
    """Add a single recipe to the PDF."""
    # Recipe title
    pdf.set_font(FONT_FAMILY, "B", FONT_SIZE_TITLE)
    pdf.set_text_color(*COLOR_PRIMARY_TEXT)
    pdf.multi_cell(0, 10, _clean_text(schema_recipe.get("name", "Untitled Recipe")))

    # Underline
    pdf.set_draw_color(*COLOR_BORDER)
    pdf.set_line_width(0.5)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 180, pdf.get_y())
    pdf.ln(5)

    # Description
    if schema_recipe.get("description"):
        pdf.set_font(FONT_FAMILY, "I", FONT_SIZE_DESCRIPTION)
        pdf.set_text_color(*COLOR_SECONDARY_TEXT)
        pdf.multi_cell(0, 6, _clean_text(schema_recipe["description"]))
        pdf.ln(3)

    # Metadata box
    metadata_items = _collect_metadata(schema_recipe)
    if metadata_items:
        _add_metadata_box(pdf, metadata_items)
        pdf.ln(5)

    # Ingredients
    if schema_recipe.get("recipeIngredient"):
        _add_section_header(pdf, "Ingredients")
        pdf.set_font(FONT_FAMILY, "", FONT_SIZE_BODY)
        pdf.set_text_color(*COLOR_BODY_TEXT)
        for ingredient in schema_recipe["recipeIngredient"]:
            # Calculate available width accounting for margins and indentation
            indent = 5
            left_margin = pdf.l_margin
            right_margin = pdf.r_margin
            page_width = pdf.w
            available_width = page_width - left_margin - right_margin - indent

            pdf.set_x(left_margin + indent)  # Indent for bullet
            pdf.multi_cell(available_width, 6, f"- {_clean_text(ingredient)}")
            pdf.set_x(left_margin)  # Reset to left margin for next item
        pdf.ln(3)

    # Equipment
    if schema_recipe.get("equipment"):
        equipment = schema_recipe["equipment"]
        equipment_list = equipment if isinstance(equipment, list) else [equipment]

        _add_section_header(pdf, "Equipment")
        pdf.set_font(FONT_FAMILY, "", FONT_SIZE_BODY)
        pdf.set_text_color(*COLOR_BODY_TEXT)
        for item in equipment_list:
            # Calculate available width accounting for margins and indentation
            indent = 5
            left_margin = pdf.l_margin
            right_margin = pdf.r_margin
            page_width = pdf.w
            available_width = page_width - left_margin - right_margin - indent

            pdf.set_x(left_margin + indent)  # Indent for bullet
            pdf.multi_cell(available_width, 6, f"- {_clean_text(item)}")
            pdf.set_x(left_margin)  # Reset to left margin for next item
        pdf.ln(3)

    # Instructions
    if schema_recipe.get("recipeInstructions"):
        _add_section_header(pdf, "Instructions")
        instructions = schema_recipe["recipeInstructions"]

        if isinstance(instructions, list):
            pdf.set_font(FONT_FAMILY, "", FONT_SIZE_BODY)
            pdf.set_text_color(*COLOR_BODY_TEXT)
            for i, step in enumerate(instructions, 1):
                step_text = step.get("text", str(step)) if isinstance(step, dict) else str(step)

                # Calculate available width accounting for margins and indentation
                indent = 5
                left_margin = pdf.l_margin
                right_margin = pdf.r_margin
                page_width = pdf.w
                available_width = page_width - left_margin - right_margin - indent

                pdf.set_x(left_margin + indent)  # Indent for number
                pdf.multi_cell(available_width, 6, f"{i}. {_clean_text(step_text)}")
                pdf.set_x(left_margin)  # Reset to left margin for next item
        elif isinstance(instructions, str):
            pdf.set_font(FONT_FAMILY, "", FONT_SIZE_BODY)
            pdf.multi_cell(0, 6, _clean_text(instructions))

        pdf.ln(3)

    # Notes
    if schema_recipe.get("notes"):
        _add_section_header(pdf, "Notes")
        pdf.set_font(FONT_FAMILY, "", FONT_SIZE_BODY)
        pdf.set_text_color(*COLOR_BODY_TEXT)
        pdf.multi_cell(0, 6, _clean_text(schema_recipe["notes"]))
        pdf.ln(3)

    # Nutrition
    nutrition = schema_recipe.get("nutrition")
    if nutrition and isinstance(nutrition, dict):
        nutrition_items = [(key, value) for key, value in nutrition.items() if value]
        if nutrition_items:
            _add_section_header(pdf, "Nutrition Information")
            pdf.set_font(FONT_FAMILY, "", FONT_SIZE_BODY)
            pdf.set_text_color(*COLOR_BODY_TEXT)

            # Display in two columns
            col_width = 90
            for key, value in nutrition_items:
                label = "".join([" " + c if c.isupper() else c for c in key]).strip().title()
                pdf.cell(col_width, 6, f"{label}: {_clean_text(str(value))}")
                pdf.ln(6)


def _add_section_header(pdf: FPDF, title: str):
    """Add a section header."""
    pdf.set_font(FONT_FAMILY, "B", FONT_SIZE_SECTION_HEADER)
    pdf.set_text_color(*COLOR_PRIMARY_TEXT)
    pdf.cell(0, 8, title, ln=True)
    pdf.ln(2)


def _add_metadata_box(pdf: FPDF, items: list[tuple[str, str]]):
    """Add metadata box with light background."""
    # Save position
    x = pdf.get_x()
    y = pdf.get_y()

    # Calculate box height
    line_height = 6
    padding = 5
    box_height = len(items) * line_height + 2 * padding

    # Draw background box
    pdf.set_fill_color(*COLOR_BACKGROUND)
    pdf.set_draw_color(*COLOR_ACCENT)
    pdf.set_line_width(1)
    pdf.rect(x, y, 180, box_height, "DF")

    # Add text
    pdf.set_xy(x + padding + 2, y + padding)
    pdf.set_font(FONT_FAMILY, "", FONT_SIZE_BODY)
    pdf.set_text_color(*COLOR_BODY_TEXT)

    for label, value in items:
        pdf.set_font(FONT_FAMILY, "B", FONT_SIZE_BODY)
        pdf.cell(30, line_height, f"{label}:")
        pdf.set_font(FONT_FAMILY, "", FONT_SIZE_BODY)
        pdf.cell(0, line_height, _clean_text(value), ln=True)
        pdf.set_x(x + padding + 2)

    # Move cursor below box
    pdf.set_xy(x, y + box_height)


def _collect_metadata(schema_recipe: dict[str, Any]) -> list[tuple[str, str]]:
    """Collect metadata items from recipe."""
    items = []

    if schema_recipe.get("recipeYield"):
        items.append(("Yield", str(schema_recipe["recipeYield"])))

    if schema_recipe.get("prepTime"):
        items.append(("Prep Time", schema_recipe["prepTime"]))

    if schema_recipe.get("cookTime"):
        items.append(("Cook Time", schema_recipe["cookTime"]))

    if schema_recipe.get("totalTime"):
        items.append(("Total Time", schema_recipe["totalTime"]))

    if schema_recipe.get("recipeCategory"):
        categories = schema_recipe["recipeCategory"]
        category_str = ", ".join(categories) if isinstance(categories, list) else str(categories)
        items.append(("Category", category_str))

    if schema_recipe.get("recipeCuisine"):
        cuisines = schema_recipe["recipeCuisine"]
        cuisine_str = ", ".join(cuisines) if isinstance(cuisines, list) else str(cuisines)
        items.append(("Cuisine", cuisine_str))

    if schema_recipe.get("keywords"):
        items.append(("Keywords", schema_recipe["keywords"]))

    if schema_recipe.get("url"):
        items.append(("Source", schema_recipe["url"]))

    return items


def _clean_text(text: str) -> str:
    """
    Clean and unescape HTML entities in text for PDF output.

    Args:
        text: Text that may contain HTML entities

    Returns:
        Cleaned text safe for PDF
    """
    if not isinstance(text, str):
        text = str(text)

    # Unescape HTML entities
    text = html.unescape(text)

    # Remove any remaining problematic characters
    # fpdf2 handles most characters well, but we'll strip control chars
    text = "".join(char for char in text if ord(char) >= 32 or char in "\n\r\t")

    return text
