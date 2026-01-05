"""
PDF export utility for recipes and collections using fpdf2.
"""

import html
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fpdf import FPDF, XPos, YPos

from app.core.config import settings
from app.core.constants import (
    PDF_AUTO_PAGE_BREAK_MARGIN,
    PDF_BOX_WIDTH,
    PDF_COLUMN_WIDTH,
    PDF_COVER_VERTICAL_POSITION,
    PDF_FOOTER_Y_POSITION,
    PDF_INDENT,
    PDF_LABEL_WIDTH,
    PDF_LINE_HEIGHT,
    PDF_LINE_WIDTH_NORMAL,
    PDF_LINE_WIDTH_THIN,
    PDF_MARGIN,
    PDF_MIN_CHAR_CODE,
    PDF_PADDING,
    PDF_TOC_MIN_RECIPES,
)
from app.core.logging import get_logger
from app.utils.recipe_format import convert_to_schema_org


if TYPE_CHECKING:
    from app.models.recipe import Recipe


# Logger for PDF export utilities
logger = get_logger(__name__)

# Font asset detection
_FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


def _locate_unicode_font() -> tuple[Path, Path | None, Path | None, str] | None:
    """Locate a preferred Unicode font and its optional bold/italic variants.

    Returns tuple (regular_path, bold_path_or_None, italic_path_or_None, family_name) or None.
    """
    for fname in settings.PDF_UNICODE_FONTS:
        candidate = _FONT_DIR / fname
        if candidate.exists():
            # Normalize base name. If file is Named like 'NotoSans-Regular', strip the '-Regular' suffix
            stem = candidate.stem
            base = stem
            if stem.lower().endswith("regular"):
                base = stem[: -len("regular")]
                base = base.rstrip("-_")

            parent = candidate.parent
            # Common bold/italic variants using base
            bold_candidates = [
                f"{base}-Bold.ttf",
                f"{base}Bold.ttf",
                f"{base}-B.ttf",
                f"{base}-Bold.otf",
                f"{base}Bold.otf",
            ]
            italic_candidates = [
                f"{base}-Italic.ttf",
                f"{base}Italic.ttf",
                f"{base}-Oblique.ttf",
                f"{base}-Italic.otf",
            ]

            bold_path = None
            italic_path = None
            for b in bold_candidates:
                p = parent / b
                if p.exists():
                    bold_path = p
                    break
            for it in italic_candidates:
                p = parent / it
                if p.exists():
                    italic_path = p
                    break

            # family name should not include '-Regular' suffix
            family_name = base
            logger.debug(
                "located_unicode_font",
                candidate=str(candidate),
                bold=str(bold_path),
                italic=str(italic_path),
                family=family_name,
            )
            return candidate, bold_path, italic_path, family_name
    return None


_FONT_ASSETS = _locate_unicode_font()
UNICODE_FONT_AVAILABLE = _FONT_ASSETS is not None
_NOTO_REGULAR = _FONT_ASSETS[0] if UNICODE_FONT_AVAILABLE else None
_NOTO_BOLD = _FONT_ASSETS[1] if UNICODE_FONT_AVAILABLE else None
_NOTO_ITALIC = _FONT_ASSETS[2] if UNICODE_FONT_AVAILABLE else None
_UNICODE_FONT_FAMILY = _FONT_ASSETS[3] if UNICODE_FONT_AVAILABLE else None

# Common unicode punctuation replacements to safe ASCII equivalents
_UNICODE_REPLACEMENTS = {
    "\u2019": "'",  # right single quotation mark
    "\u2018": "'",  # left single quotation mark
    "\u201c": '"',  # left double quotation mark
    "\u201d": '"',  # right double quotation mark
    "\u2013": "-",  # en dash
    "\u2014": "--",  # em dash
    "\u2026": "...",  # ellipsis
    "\u00a0": " ",  # non-breaking space
}


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
        """Initialize PDF with Unicode font if available."""
        super().__init__()
        # Use built-in Unicode font support when available
        self.set_auto_page_break(auto=True, margin=PDF_AUTO_PAGE_BREAK_MARGIN)

        if UNICODE_FONT_AVAILABLE:
            try:
                # Register detected font family (regular + bold/italic if present)
                font_name = _UNICODE_FONT_FAMILY or "CustomUnicode"
                # Register regular font using explicit keyword args per fpdf2 docs to avoid
                # using the deprecated 'uni' parameter. Fall back to older positional
                # signatures if necessary for compatibility with older fpdf2 versions.
                try:
                    self.add_font(family=font_name, style="", fname=str(_NOTO_REGULAR))
                except TypeError:
                    try:
                        # Positional: family, style, fname
                        self.add_font(font_name, "", str(_NOTO_REGULAR))
                    except TypeError:
                        # Older variant: family, fname
                        self.add_font(font_name, str(_NOTO_REGULAR))

                # Bold
                if _NOTO_BOLD and _NOTO_BOLD.exists():
                    try:
                        self.add_font(family=font_name, style="B", fname=str(_NOTO_BOLD))
                    except TypeError:
                        try:
                            self.add_font(font_name, "B", str(_NOTO_BOLD))
                        except TypeError:
                            self.add_font(font_name, str(_NOTO_BOLD))

                # Italic
                if _NOTO_ITALIC and _NOTO_ITALIC.exists():
                    try:
                        self.add_font(family=font_name, style="I", fname=str(_NOTO_ITALIC))
                    except TypeError:
                        try:
                            self.add_font(font_name, "I", str(_NOTO_ITALIC))
                        except TypeError:
                            self.add_font(font_name, str(_NOTO_ITALIC))

                self.font_family = font_name
            except (OSError, RuntimeError, ValueError) as e:
                logger.exception("failed_to_register_unicode_font", error=str(e))
                # Fall back to core font
                self.font_family = "Helvetica"
        else:
            self.font_family = "Helvetica"

        # Set a default font so measurements work consistently
        self.set_font(self.font_family, "", FONT_SIZE_BODY)

    def header(self):
        """Add header to each page (empty for now)."""

    def footer(self):
        """Add page numbers to footer."""
        self.set_y(PDF_FOOTER_Y_POSITION)
        self.set_font(self.font_family, "I", FONT_SIZE_FOOTER)
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
    pdf.set_auto_page_break(auto=True, margin=PDF_MARGIN)

    # Add recipe content
    _add_recipe_to_pdf(pdf, schema_recipe)

    # Return PDF as bytes
    output = pdf.output()
    return bytes(output) if not isinstance(output, bytes) else output


def generate_collection_pdf(collection_name: str, collection_description: str, recipes: list["Recipe"]) -> bytes:
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
    pdf.set_auto_page_break(auto=True, margin=PDF_MARGIN)

    # Add cover page
    pdf.add_page()
    _add_collection_cover(pdf, collection_name, collection_description)

    # Add table of contents
    if len(recipes) > PDF_TOC_MIN_RECIPES:
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
    pdf.set_y(PDF_COVER_VERTICAL_POSITION)

    # Collection title
    pdf.set_font(pdf.font_family, "B", FONT_SIZE_COVER_TITLE)
    pdf.set_text_color(*COLOR_PRIMARY_TEXT)
    pdf.multi_cell(0, 15, _clean_text(name), align="C")

    # Description
    if description:
        pdf.ln(10)
        pdf.set_font(pdf.font_family, "", FONT_SIZE_DESCRIPTION)
        pdf.set_text_color(*COLOR_SECONDARY_TEXT)
        pdf.multi_cell(0, 8, _clean_text(description), align="C")


def _add_table_of_contents(pdf: FPDF, recipes: list["Recipe"]):
    """Add table of contents page."""
    pdf.set_font(pdf.font_family, "B", FONT_SIZE_TOC_TITLE)
    pdf.set_text_color(*COLOR_PRIMARY_TEXT)
    pdf.cell(0, 12, "Table of Contents", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    # Draw underline
    pdf.set_draw_color(*COLOR_BORDER)
    pdf.set_line_width(PDF_LINE_WIDTH_THIN)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + PDF_BOX_WIDTH, pdf.get_y())
    pdf.ln(8)

    # List recipes
    pdf.set_font(pdf.font_family, "", FONT_SIZE_TOC_BODY)
    pdf.set_text_color(*COLOR_BODY_TEXT)
    for i, recipe in enumerate(recipes, 1):
        pdf.cell(10, 8, f"{i}.")
        pdf.multi_cell(0, 8, _clean_text(recipe.name))


def _add_recipe_to_pdf(pdf: FPDF, schema_recipe: dict[str, Any]):
    """Add a single recipe to the PDF."""
    # Recipe title
    pdf.set_font(pdf.font_family, "B", FONT_SIZE_TITLE)
    pdf.set_text_color(*COLOR_PRIMARY_TEXT)
    pdf.multi_cell(0, 10, _clean_text(schema_recipe.get("name", "Untitled Recipe")))

    # Underline
    pdf.set_draw_color(*COLOR_BORDER)
    pdf.set_line_width(PDF_LINE_WIDTH_THIN)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + PDF_BOX_WIDTH, pdf.get_y())
    pdf.ln(5)

    # Description
    if schema_recipe.get("description"):
        pdf.set_font(pdf.font_family, "I", FONT_SIZE_DESCRIPTION)
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
        pdf.set_font(pdf.font_family, "", FONT_SIZE_BODY)
        pdf.set_text_color(*COLOR_BODY_TEXT)
        for ingredient in schema_recipe["recipeIngredient"]:
            # Calculate available width accounting for margins and indentation
            indent = PDF_INDENT
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
        pdf.set_font(pdf.font_family, "", FONT_SIZE_BODY)
        pdf.set_text_color(*COLOR_BODY_TEXT)
        for item in equipment_list:
            # Calculate available width accounting for margins and indentation
            indent = PDF_INDENT
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
            pdf.set_font(pdf.font_family, "", FONT_SIZE_BODY)
            pdf.set_text_color(*COLOR_BODY_TEXT)
            for i, step in enumerate(instructions, 1):
                step_text = step.get("text", str(step)) if isinstance(step, dict) else str(step)

                # Calculate available width accounting for margins and indentation
                indent = PDF_INDENT
                left_margin = pdf.l_margin
                right_margin = pdf.r_margin
                page_width = pdf.w
                available_width = page_width - left_margin - right_margin - indent

                pdf.set_x(left_margin + indent)  # Indent for number
                pdf.multi_cell(available_width, 6, f"{i}. {_clean_text(step_text)}")
                pdf.set_x(left_margin)  # Reset to left margin for next item
        elif isinstance(instructions, str):
            pdf.set_font(pdf.font_family, "", FONT_SIZE_BODY)
            pdf.multi_cell(0, 6, _clean_text(instructions))

        pdf.ln(3)

    # Notes
    if schema_recipe.get("notes"):
        _add_section_header(pdf, "Notes")
        pdf.set_font(pdf.font_family, "", FONT_SIZE_BODY)
        pdf.set_text_color(*COLOR_BODY_TEXT)
        pdf.multi_cell(0, 6, _clean_text(schema_recipe["notes"]))
        pdf.ln(3)

    # Nutrition
    nutrition = schema_recipe.get("nutrition")
    if nutrition and isinstance(nutrition, dict):
        nutrition_items = [(key, value) for key, value in nutrition.items() if value]
        if nutrition_items:
            _add_section_header(pdf, "Nutrition Information")
            pdf.set_font(pdf.font_family, "", FONT_SIZE_BODY)
            pdf.set_text_color(*COLOR_BODY_TEXT)

            # Display in two columns
            col_width = PDF_COLUMN_WIDTH
            for key, value in nutrition_items:
                label = "".join([" " + c if c.isupper() else c for c in key]).strip().title()
                pdf.cell(col_width, 6, f"{label}: {_clean_text(str(value))}")
                pdf.ln(6)


def _add_section_header(pdf: FPDF, title: str):
    """Add a section header."""
    pdf.set_font(pdf.font_family, "B", FONT_SIZE_SECTION_HEADER)
    pdf.set_text_color(*COLOR_PRIMARY_TEXT)
    pdf.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)


def _add_metadata_box(pdf: FPDF, items: list[tuple[str, str]]):
    """Add metadata box with light background."""
    # Save position
    x = pdf.get_x()
    y = pdf.get_y()

    # Calculate box height
    line_height = PDF_LINE_HEIGHT
    padding = PDF_PADDING
    box_height = len(items) * line_height + 2 * padding

    # Draw background box
    pdf.set_fill_color(*COLOR_BACKGROUND)
    pdf.set_draw_color(*COLOR_ACCENT)
    pdf.set_line_width(PDF_LINE_WIDTH_NORMAL)
    pdf.rect(x, y, PDF_BOX_WIDTH, box_height, "DF")

    # Add text
    pdf.set_xy(x + padding + 2, y + padding)
    pdf.set_font(pdf.font_family, "", FONT_SIZE_BODY)
    pdf.set_text_color(*COLOR_BODY_TEXT)

    for label, value in items:
        pdf.set_font(FONT_FAMILY, "B", FONT_SIZE_BODY)
        pdf.cell(PDF_LABEL_WIDTH, line_height, f"{label}:")
        pdf.set_font(FONT_FAMILY, "", FONT_SIZE_BODY)
        pdf.cell(0, line_height, _clean_text(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


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


def _replace_unicode_punctuation(text: str) -> tuple[str, bool]:
    """Replace common Unicode punctuation with ASCII equivalents.

    Returns a tuple of (new_text, changed_flag).
    """
    changed = False
    for uni_char, repl in _UNICODE_REPLACEMENTS.items():
        if uni_char in text:
            text = text.replace(uni_char, repl)
            changed = True
    return text, changed


def _clean_text(text: str) -> str:
    """
    Clean and unescape HTML entities in text for PDF output.

    - Unescape HTML entities
    - Replace common Unicode punctuation with ASCII equivalents
    - Remove control characters
    - Replace characters outside the Latin-1 range with '?'

    Args:
        text: Text that may contain HTML entities

    Returns:
        Cleaned text safe for PDF
    """
    if not isinstance(text, str):
        text = str(text)

    # Unescape HTML entities
    text = html.unescape(text)

    # Replace smart punctuation (curly quotes, dashes, ellipsis, etc.)
    text, changed = _replace_unicode_punctuation(text)
    if changed:
        logger.debug("replaced_unicode_punctuation_in_text")

    # Remove control characters (keep common whitespace)
    text = "".join(char for char in text if ord(char) >= PDF_MIN_CHAR_CODE or char in "\n\r\t")

    # fpdf (core fonts) supports Latin-1 range. Replace characters outside 0-255 with '?' to avoid fpdf errors.
    cleaned_chars = []
    replaced_any = False
    for char in text:
        code = ord(char)
        if code > 255:
            cleaned_chars.append("?")
            replaced_any = True
        else:
            cleaned_chars.append(char)
    if replaced_any:
        logger.warning("replaced_non_latin1_chars_in_text")

    return "".join(cleaned_chars)
