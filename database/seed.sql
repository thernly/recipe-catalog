-- Seed data for testing
-- This file contains sample data for development and testing

-- Note: In production, default collections should be created via the API
-- when a user registers. This is just for testing.

-- Sample user (password is 'testpassword123')
-- INSERT INTO users (email, hashed_password, display_name, is_active, is_verified)
-- VALUES ('test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ByJ3JlT/xRii', 'Test User', 1, 1);

-- Sample collections for the test user
-- INSERT INTO collections (user_id, name, description, is_default, icon)
-- VALUES
--     (1, 'All Recipes', 'All your recipes', 1, '📚'),
--     (1, 'Favorites', 'Your favorite recipes', 1, '⭐'),
--     (1, 'Quick Meals', 'Recipes under 30 minutes', 0, '⚡'),
--     (1, 'Desserts', 'Sweet treats and desserts', 0, '🍰');

-- Sample recipe data
-- INSERT INTO recipes (user_id, name, description, image_url, recipe_data, source_type, cuisine, category, total_time_minutes)
-- VALUES (
--     1,
--     'Simple Scrambled Eggs',
--     'Quick and easy breakfast scrambled eggs',
--     NULL,
--     '{"name":"Simple Scrambled Eggs","recipeIngredient":["4 eggs","2 tbsp butter","Salt and pepper to taste","2 tbsp milk (optional)"],"recipeInstructions":["Crack eggs into a bowl and whisk with milk if using","Heat butter in a non-stick pan over medium heat","Pour in eggs and let sit for 20 seconds","Gently stir and fold until just set","Season with salt and pepper"],"prepTime":"PT5M","cookTime":"PT5M","totalTime":"PT10M","recipeYield":"2 servings"}',
--     'manual',
--     'American',
--     'Breakfast',
--     10
-- );

-- You can add more sample recipes here for testing
