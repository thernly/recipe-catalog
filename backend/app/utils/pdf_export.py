"""
PDF export utility for recipes and collections.
"""

from typing import Any

from weasyprint import CSS, HTML

from app.utils.recipe_format import convert_to_schema_org


def generate_recipe_pdf(recipe: Any) -> bytes:
    """
    Generate a PDF for a single recipe.

    Args:
        recipe: Recipe model instance

    Returns:
        bytes: PDF file content
    """
    # Convert recipe to schema.org format
    schema_recipe = convert_to_schema_org(recipe)

    # Generate HTML content
    html_content = _generate_recipe_html(schema_recipe)

    # Convert HTML to PDF
    pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[CSS(string=_get_pdf_styles())])

    return pdf_bytes


def generate_collection_pdf(
    collection_name: str, collection_description: str, recipes: list[Any]
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
    # Generate HTML content for all recipes
    html_parts = [_generate_collection_header(collection_name, collection_description)]

    # Add table of contents
    if len(recipes) > 1:
        html_parts.append(_generate_table_of_contents(recipes))

    # Add each recipe
    for recipe in recipes:
        schema_recipe = convert_to_schema_org(recipe)
        html_parts.append(_generate_recipe_html(schema_recipe, include_page_break=True))

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{collection_name}</title>
    </head>
    <body>
        {"".join(html_parts)}
    </body>
    </html>
    """

    # Convert HTML to PDF
    pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[CSS(string=_get_pdf_styles())])

    return pdf_bytes


def _generate_collection_header(name: str, description: str) -> str:
    """Generate HTML for collection cover page."""
    desc_html = (
        f"<p class='collection-description'>{_escape_html(description)}</p>" if description else ""
    )

    return f"""
    <div class="collection-cover">
        <h1 class="collection-title">{_escape_html(name)}</h1>
        {desc_html}
    </div>
    """


def _generate_table_of_contents(recipes: list[Any]) -> str:
    """Generate HTML for table of contents."""
    recipe_items = []
    for i, recipe in enumerate(recipes, 1):
        recipe_items.append(f"<li>{i}. {_escape_html(recipe.name)}</li>")

    return f"""
    <div class="table-of-contents">
        <h2>Table of Contents</h2>
        <ol class="toc-list">
            {"".join(recipe_items)}
        </ol>
    </div>
    <div class="page-break"></div>
    """


def _generate_recipe_html(schema_recipe: dict, include_page_break: bool = False) -> str:
    """
    Generate HTML for a single recipe.

    Args:
        schema_recipe: Recipe in schema.org format
        include_page_break: Whether to add a page break before the recipe

    Returns:
        str: HTML content
    """
    page_break = '<div class="page-break"></div>' if include_page_break else ""

    # Recipe title and description
    title = _escape_html(schema_recipe.get("name", "Untitled Recipe"))
    description = schema_recipe.get("description", "")
    description_html = (
        f"<p class='description'>{_escape_html(description)}</p>" if description else ""
    )

    # Metadata section
    metadata_items = []
    if schema_recipe.get("recipeYield"):
        metadata_items.append(
            f"<div class='meta-item'><strong>Yield:</strong> {_escape_html(str(schema_recipe['recipeYield']))}</div>"
        )
    if schema_recipe.get("prepTime"):
        metadata_items.append(
            f"<div class='meta-item'><strong>Prep Time:</strong> {_escape_html(schema_recipe['prepTime'])}</div>"
        )
    if schema_recipe.get("cookTime"):
        metadata_items.append(
            f"<div class='meta-item'><strong>Cook Time:</strong> {_escape_html(schema_recipe['cookTime'])}</div>"
        )
    if schema_recipe.get("totalTime"):
        metadata_items.append(
            f"<div class='meta-item'><strong>Total Time:</strong> {_escape_html(schema_recipe['totalTime'])}</div>"
        )
    if schema_recipe.get("recipeCategory"):
        categories = schema_recipe["recipeCategory"]
        category_str = ", ".join(categories) if isinstance(categories, list) else str(categories)
        metadata_items.append(
            f"<div class='meta-item'><strong>Category:</strong> {_escape_html(category_str)}</div>"
        )
    if schema_recipe.get("recipeCuisine"):
        cuisines = schema_recipe["recipeCuisine"]
        cuisine_str = ", ".join(cuisines) if isinstance(cuisines, list) else str(cuisines)
        metadata_items.append(
            f"<div class='meta-item'><strong>Cuisine:</strong> {_escape_html(cuisine_str)}</div>"
        )
    if schema_recipe.get("keywords"):
        metadata_items.append(
            f"<div class='meta-item'><strong>Keywords:</strong> {_escape_html(schema_recipe['keywords'])}</div>"
        )
    if schema_recipe.get("url"):
        metadata_items.append(
            f"<div class='meta-item'><strong>Source:</strong> {_escape_html(schema_recipe['url'])}</div>"
        )

    metadata_html = (
        f"<div class='metadata'>{''.join(metadata_items)}</div>" if metadata_items else ""
    )

    # Ingredients
    ingredients_html = ""
    if schema_recipe.get("recipeIngredient"):
        ingredient_items = [
            f"<li>{_escape_html(ing)}</li>" for ing in schema_recipe["recipeIngredient"]
        ]
        ingredients_html = f"""
        <div class='section'>
            <h2>Ingredients</h2>
            <ul class='ingredients-list'>
                {"".join(ingredient_items)}
            </ul>
        </div>
        """

    # Equipment
    equipment_html = ""
    if schema_recipe.get("equipment"):
        equipment = schema_recipe["equipment"]
        if isinstance(equipment, list):
            equipment_items = [f"<li>{_escape_html(item)}</li>" for item in equipment]
            equipment_html = f"""
            <div class='section'>
                <h2>Equipment</h2>
                <ul>
                    {"".join(equipment_items)}
                </ul>
            </div>
            """
        elif isinstance(equipment, str):
            equipment_html = f"""
            <div class='section'>
                <h2>Equipment</h2>
                <ul>
                    <li>{_escape_html(equipment)}</li>
                </ul>
            </div>
            """

    # Instructions
    instructions_html = ""
    if schema_recipe.get("recipeInstructions"):
        instructions = schema_recipe["recipeInstructions"]
        if isinstance(instructions, list):
            instruction_items = []
            for i, step in enumerate(instructions, 1):
                if isinstance(step, dict):
                    step_text = step.get("text", str(step))
                else:
                    step_text = str(step)
                instruction_items.append(f"<li>{_escape_html(step_text)}</li>")
            instructions_html = f"""
            <div class='section'>
                <h2>Instructions</h2>
                <ol class='instructions-list'>
                    {"".join(instruction_items)}
                </ol>
            </div>
            """
        elif isinstance(instructions, str):
            instructions_html = f"""
            <div class='section'>
                <h2>Instructions</h2>
                <p>{_escape_html(instructions)}</p>
            </div>
            """

    # Notes
    notes_html = ""
    if schema_recipe.get("notes"):
        notes_html = f"""
        <div class='section'>
            <h2>Notes</h2>
            <p>{_escape_html(schema_recipe["notes"])}</p>
        </div>
        """

    # Nutrition
    nutrition_html = ""
    if schema_recipe.get("nutrition"):
        nutrition = schema_recipe["nutrition"]
        if isinstance(nutrition, dict) and nutrition:
            nutrition_items = []
            for key, value in nutrition.items():
                if value:
                    label = "".join([" " + c if c.isupper() else c for c in key]).strip().title()
                    nutrition_items.append(
                        f"<div class='nutrition-item'><strong>{_escape_html(label)}:</strong> {_escape_html(str(value))}</div>"
                    )
            if nutrition_items:
                nutrition_html = f"""
                <div class='section'>
                    <h2>Nutrition Information</h2>
                    <div class='nutrition-info'>
                        {"".join(nutrition_items)}
                    </div>
                </div>
                """

    # Assemble complete recipe HTML
    return f"""
    {page_break}
    <div class="recipe">
        <h1 class="recipe-title">{title}</h1>
        {description_html}
        {metadata_html}
        {ingredients_html}
        {equipment_html}
        {instructions_html}
        {notes_html}
        {nutrition_html}
    </div>
    """


def _get_pdf_styles() -> str:
    """Get CSS styles for PDF output."""
    return """
    @page {
        size: Letter;
        margin: 1in;
    }

    body {
        font-family: Georgia, serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333;
    }

    .page-break {
        page-break-before: always;
    }

    .collection-cover {
        text-align: center;
        padding: 3in 1in;
        page-break-after: always;
    }

    .collection-title {
        font-size: 36pt;
        margin-bottom: 0.5in;
        color: #2c3e50;
    }

    .collection-description {
        font-size: 14pt;
        color: #555;
        max-width: 5in;
        margin: 0 auto;
    }

    .table-of-contents {
        margin: 2em 0;
    }

    .table-of-contents h2 {
        font-size: 24pt;
        margin-bottom: 1em;
        color: #2c3e50;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 0.25em;
    }

    .toc-list {
        list-style: none;
        padding-left: 0;
    }

    .toc-list li {
        padding: 0.5em 0;
        font-size: 12pt;
    }

    .recipe {
        margin-bottom: 2em;
    }

    .recipe-title {
        font-size: 24pt;
        margin-bottom: 0.5em;
        color: #2c3e50;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 0.25em;
    }

    .description {
        font-style: italic;
        color: #555;
        margin: 1em 0;
    }

    .metadata {
        background: #f8f9fa;
        border-left: 4px solid #3498db;
        padding: 1em;
        margin: 1em 0;
    }

    .meta-item {
        margin: 0.25em 0;
    }

    .section {
        margin: 1.5em 0;
    }

    .section h2 {
        font-size: 16pt;
        margin-bottom: 0.75em;
        color: #2c3e50;
    }

    .ingredients-list,
    .instructions-list {
        margin: 0;
        padding-left: 1.5em;
    }

    .ingredients-list li,
    .instructions-list li {
        margin: 0.5em 0;
    }

    .nutrition-info {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.5em;
    }

    .nutrition-item {
        padding: 0.25em 0;
    }

    ul {
        list-style-type: disc;
    }

    ol {
        list-style-type: decimal;
    }
    """


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    if not isinstance(text, str):
        text = str(text)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
