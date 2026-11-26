import { describe, it, expect } from "vitest";
import { scaleIngredient } from "./scale-ingredient.js";

describe("scaleIngredient", () => {
  it.each([
    // line, factor, expected
    ["2 eggs", 2, "4 eggs"],
    ["1 1/2 cups flour", 2, "3 cups flour"],
    ["3/4 cup sugar", 2, "1 1/2 cup sugar"],
    ["1 cup milk", 0.5, "1/2 cup milk"],
    ["1/3 cup oil", 2, "2/3 cup oil"],
    ["½ tsp salt", 3, "1 1/2 tsp salt"],
    ["1½ cups stock", 2, "3 cups stock"],
    ["2-3 cloves garlic", 2, "4-6 cloves garlic"],
    ["2 to 3 tomatoes", 3, "6 to 9 tomatoes"],
    ["2 tomatoes", 2, "4 tomatoes"],
    ["100g plain flour", 1.5, "150g plain flour"],
    ["125g butter", 0.5, "62.5g butter"],
    ["0.5 kg beef", 3, "1.5 kg beef"],
    ["1 egg", 0.5, "1/2 egg"],
    ["3 eggs", 0.5, "1 1/2 eggs"],
  ])("%s x %s -> %s", (line, factor, expected) => {
    expect(scaleIngredient(line, factor)).toBe(expected);
  });

  it("leaves a line alone at 1x, or when it does not start with an amount", () => {
    expect(scaleIngredient("½ tsp salt", 1)).toBe("½ tsp salt");
    expect(scaleIngredient("Salt, to taste", 2)).toBe("Salt, to taste");
    expect(scaleIngredient("Juice of 2 lemons", 2)).toBe("Juice of 2 lemons");
  });

  it("never scales a group heading", () => {
    expect(
      scaleIngredient("2 layers:", 2, { raw: "2 layers:", header: true }),
    ).toBe("2 layers:");
  });

  it("makes a spelled-out unit agree with the new amount", () => {
    const cup = { raw: "", unit: "cup" };
    expect(scaleIngredient("1 cup milk", 2, cup)).toBe("2 cups milk");
    expect(scaleIngredient("2 cups milk", 0.5, cup)).toBe("1 cup milk");
    expect(scaleIngredient("1 cup milk", 0.5, cup)).toBe("1/2 cup milk");
    expect(scaleIngredient("1 Cup milk", 3, cup)).toBe("3 cups milk");
    expect(scaleIngredient("1 pinch salt", 2, { raw: "", unit: "pinch" })).toBe(
      "2 pinches salt",
    );
  });

  it("scales the same amount given again in brackets after the unit", () => {
    const cup = { raw: "", unit: "cup" };
    expect(scaleIngredient("2/3 cup (142g) light brown sugar", 2, cup)).toBe(
      "1 1/3 cups (284g) light brown sugar",
    );
    expect(scaleIngredient("1 cup (4 1/4 ounces) flour", 2, cup)).toBe(
      "2 cups (8 1/2 ounces) flour",
    );
    expect(
      scaleIngredient("1 tbsp (15 ml) oil", 3, { raw: "", unit: "tablespoon" }),
    ).toBe("3 tbsp (45 ml) oil");
    expect(
      scaleIngredient("100g (3.5oz) butter", 2, { raw: "", unit: "gram" }),
    ).toBe("200g (7oz) butter");
  });

  it("leaves other brackets alone", () => {
    // A size, not a second way of writing the amount
    expect(
      scaleIngredient("2 (14-ounce) cans tomatoes", 2, {
        raw: "",
        unit: "can",
      }),
    ).toBe("4 (14-ounce) cans tomatoes");
    expect(scaleIngredient("1 large (150g) onion", 2, { raw: "" })).toBe(
      "2 large (150g) onion",
    );
    expect(
      scaleIngredient("3/4 teaspoon salt, (use 1/2 teaspoon if salted)", 2, {
        raw: "",
        unit: "teaspoon",
      }),
    ).toBe("1 1/2 teaspoons salt, (use 1/2 teaspoon if salted)");
    expect(
      scaleIngredient("1 cup (see note) stock", 2, { raw: "", unit: "cup" }),
    ).toBe("2 cups (see note) stock");
  });

  it("leaves an abbreviated unit as written", () => {
    const tbsp = { raw: "", unit: "tablespoon" };
    expect(scaleIngredient("1 tbsp oil", 2, tbsp)).toBe("2 tbsp oil");
    expect(scaleIngredient("100g flour", 2, { raw: "", unit: "gram" })).toBe(
      "200g flour",
    );
  });
});
