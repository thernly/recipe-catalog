"""
AI service for recipe generation using OpenRouter API.
"""

import logging
from typing import Any

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered recipe generation."""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = settings.OPENROUTER_MODEL or "anthropic/claude-3.5-sonnet"

    async def generate_recipe(
        self,
        ingredients: list[str],
        cuisine: str | None = None,
        time_limit: int | None = None,
        dietary_preferences: list[str] | None = None,
        equipment: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate a recipe from ingredients using AI.

        Args:
            ingredients: List of available ingredients
            cuisine: Optional cuisine type (e.g., "Italian", "Mexican")
            time_limit: Optional time limit in minutes
            dietary_preferences: Optional list of dietary preferences (e.g., ["vegetarian", "gluten-free"])
            equipment: Optional list of available equipment

        Returns:
            Dict containing generated recipe data

        Raises:
            Exception: If AI generation fails
        """
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not configured. Please set it in environment variables."
            )

        # Build the prompt
        prompt = self._build_prompt(
            ingredients, cuisine, time_limit, dietary_preferences, equipment
        )

        # Call OpenRouter API
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": settings.FRONTEND_URL,
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a professional chef assistant. Generate creative, safe, and delicious recipes based on available ingredients. Always respond with valid JSON only.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.7,
                    },
                )
                response.raise_for_status()
                result = response.json()

                # Extract the generated content
                content = result["choices"][0]["message"]["content"]

                # Parse the JSON response
                import json

                recipe_data = json.loads(content)

                # Log usage for monitoring (without sensitive data)
                logger.info(
                    f"AI recipe generated successfully. Tokens used: {result.get('usage', {}).get('total_tokens', 'unknown')}"
                )

                return recipe_data

            except httpx.HTTPStatusError as e:
                logger.error(f"OpenRouter API error: {e.response.status_code} - {e.response.text}")
                if e.response.status_code == 429:
                    raise Exception("Rate limit exceeded. Please try again later.")
                elif e.response.status_code == 401:
                    raise Exception("Invalid API key. Please check configuration.")
                else:
                    raise Exception(f"AI service error: {e.response.text}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI response: {content}")
                raise Exception("Failed to parse AI response. Please try again.")
            except Exception as e:
                logger.exception(f"Unexpected error during AI generation: {str(e)}")
                raise Exception(f"AI generation failed: {str(e)}")

    def _build_prompt(
        self,
        ingredients: list[str],
        cuisine: str | None,
        time_limit: int | None,
        dietary_preferences: list[str] | None,
        equipment: list[str] | None,
    ) -> str:
        """Build the prompt for recipe generation."""
        ingredients_str = ", ".join(ingredients)

        prompt = f"""Create a recipe using these ingredients: {ingredients_str}

"""

        # Add optional constraints
        if cuisine:
            prompt += f"Cuisine style: {cuisine}\n"
        if time_limit:
            prompt += f"Maximum cooking time: {time_limit} minutes\n"
        if dietary_preferences:
            prompt += f"Dietary preferences: {', '.join(dietary_preferences)}\n"
        if equipment:
            prompt += f"Available equipment: {', '.join(equipment)}\n"

        prompt += """
Please generate a complete recipe and respond with ONLY a valid JSON object (no markdown, no code blocks, just pure JSON) in this exact format:

{
  "name": "Recipe Name",
  "description": "Brief description of the dish",
  "recipeYield": "4 servings",
  "prepTime": "PT15M",
  "cookTime": "PT30M",
  "totalTime": "PT45M",
  "recipeIngredient": [
    "2 cups flour",
    "1 tsp salt",
    "etc..."
  ],
  "recipeInstructions": [
    "Step 1: Do this...",
    "Step 2: Do that...",
    "etc..."
  ],
  "recipeCategory": ["Main Course"],
  "recipeCuisine": ["Italian"],
  "keywords": "easy, quick, weeknight dinner",
  "equipment": ["oven", "mixing bowl"],
  "notes": "Optional serving suggestions or tips"
}

Important:
- Use ISO 8601 duration format for times (PT15M for 15 minutes, PT1H30M for 1 hour 30 minutes)
- Include all provided ingredients where appropriate
- Make it practical and achievable
- Ensure food safety
- Return ONLY the JSON object, nothing else
"""

        return prompt

    async def generate_menu(
        self,
        days: int,
        meals_per_day: list[str],
        dietary_preferences: list[str] | None = None,
        cuisine: str | None = None,
        mode: str = "catalog-first",
        household_recipes: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Generate menu suggestions for multiple days using AI.

        Args:
            days: Number of days to generate menu for
            meals_per_day: List of meal types (e.g., ["breakfast", "lunch", "dinner"])
            dietary_preferences: Optional list of dietary preferences
            cuisine: Optional cuisine preference
            mode: Generation mode ("catalog-first" or "ai-only")
            household_recipes: Optional list of recipes from household catalog

        Returns:
            List of meal suggestions

        Raises:
            Exception: If AI generation fails
        """
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not configured. Please set it in environment variables."
            )

        # Build the prompt
        prompt = self._build_menu_prompt(
            days, meals_per_day, dietary_preferences, cuisine, mode, household_recipes
        )

        # Call OpenRouter API
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": settings.FRONTEND_URL,
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a professional meal planning assistant. Generate creative, balanced, and practical menu suggestions. Always respond with valid JSON only.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.7,
                    },
                )
                response.raise_for_status()
                result = response.json()

                # Extract the generated content
                content = result["choices"][0]["message"]["content"]

                # Parse the JSON response
                import json

                menu_data = json.loads(content)

                # Log usage for monitoring (without sensitive data)
                logger.info(
                    f"AI menu generated successfully. Tokens used: {result.get('usage', {}).get('total_tokens', 'unknown')}"
                )

                return menu_data.get("suggestions", [])

            except httpx.HTTPStatusError as e:
                logger.error(f"OpenRouter API error: {e.response.status_code} - {e.response.text}")
                if e.response.status_code == 429:
                    raise Exception("Rate limit exceeded. Please try again later.")
                elif e.response.status_code == 401:
                    raise Exception("Invalid API key. Please check configuration.")
                else:
                    raise Exception(f"AI service error: {e.response.text}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI response: {content}")
                raise Exception("Failed to parse AI response. Please try again.")
            except Exception as e:
                logger.exception(f"Unexpected error during AI menu generation: {str(e)}")
                raise Exception(f"AI menu generation failed: {str(e)}")

    def _build_menu_prompt(
        self,
        days: int,
        meals_per_day: list[str],
        dietary_preferences: list[str] | None,
        cuisine: str | None,
        mode: str,
        household_recipes: list[dict[str, Any]] | None,
    ) -> str:
        """Build the prompt for menu generation."""
        prompt = f"""Generate a menu plan for {days} day(s) with the following meals each day: {", ".join(meals_per_day)}

"""

        # Add dietary preferences
        if dietary_preferences:
            prompt += f"Dietary preferences: {', '.join(dietary_preferences)}\n"

        # Add cuisine preference
        if cuisine:
            prompt += f"Cuisine style preference: {cuisine}\n"

        # Add mode-specific instructions
        if mode == "catalog-first" and household_recipes:
            prompt += "\nMode: Catalog-first - Prioritize using recipes from the user's catalog below:\n\n"
            for recipe in household_recipes[:50]:  # Limit to avoid token overflow
                prompt += f"- ID: {recipe.get('id')}, Name: {recipe.get('name')}, Category: {recipe.get('category', 'N/A')}\n"
            prompt += "\nIf the catalog doesn't have suitable recipes for some meals, you may suggest new recipe names.\n"
        else:
            prompt += "\nMode: AI-only - Generate creative new recipe suggestions.\n"

        prompt += """
Please generate a complete menu plan and respond with ONLY a valid JSON object (no markdown, no code blocks, just pure JSON) in this exact format:

{
  "suggestions": [
    {
      "day": 1,
      "meal_type": "breakfast",
      "recipe_id": 123,
      "recipe_name": "Scrambled Eggs with Toast",
      "description": "Simple and nutritious breakfast",
      "prep_time": "PT5M",
      "cook_time": "PT10M"
    },
    {
      "day": 1,
      "meal_type": "lunch",
      "recipe_id": null,
      "recipe_name": "Garden Salad",
      "description": "Fresh and healthy lunch",
      "prep_time": "PT10M",
      "cook_time": "PT0M"
    }
  ]
}

Important:
- Generate suggestions for all {days} day(s) and all meal types: {', '.join(meals_per_day)}
- If using catalog-first mode, set recipe_id to the ID from the catalog when using an existing recipe
- If generating new suggestions or in ai-only mode, set recipe_id to null
- Use ISO 8601 duration format for times (PT15M for 15 minutes, PT1H30M for 1 hour 30 minutes)
- Make it practical, balanced, and varied
- Respect all dietary preferences
- Return ONLY the JSON object, nothing else
"""

        return prompt


# Create a singleton instance
ai_service = AIService()
