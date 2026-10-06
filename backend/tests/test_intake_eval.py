"""Tests for the cleanup eval harness, plus the run over the real (git-ignored) eval set."""

import json
import os

import pytest

from app.services.intake_eval import (
    LINE_TARGET,
    RECIPE_TARGET,
    draft_cases,
    eval_dir_from_env,
    format_report,
    run_eval,
    write_originals,
)


RECIPES = [
    {
        "name": "Pancakes",
        "recipeYield": "4 4 servings",
        "prepTime": "10 mins",
        "recipeIngredient": ["1 cup flour", "1 egg", "Seeds scraped from 1 vanilla pod"],
    },
    {"name": "Toast", "recipeIngredient": ["2 slices bread"]},
]


@pytest.fixture
def eval_dir(tmp_path):
    (tmp_path / "inputs").mkdir()
    (tmp_path / "inputs" / "export.json").write_text(json.dumps(RECIPES))
    return tmp_path


def _load(path):
    return json.loads(path.read_text())


def _check(path, edit=None):
    case = _load(path)
    case["checked"] = True
    if edit:
        edit(case["expected"])
    path.write_text(json.dumps(case))


def test_draft_writes_unchecked_cases_from_current_output(eval_dir):
    result = draft_cases(eval_dir)

    assert sorted(p.name for p in result.written) == ["pancakes.json", "toast.json"]
    assert (result.input_files, result.recipes_found, result.already_drafted) == (1, 2, 0)
    assert result.warnings == []
    case = _load(eval_dir / "cases" / "pancakes.json")
    assert case["checked"] is False
    assert case["source"] == "inputs/export.json#0"
    assert case["input"] == RECIPES[0]
    assert case["expected"]["recipeYield"] == "4 servings"
    assert case["expected"]["prepTime"] == "PT10M"
    assert case["expected"]["parsedIngredients"][0] == {
        "raw": "1 cup flour",
        "quantity": 1,
        "quantityMax": None,
        "unit": "cup",
        "item": "flour",
        "note": None,
        "group": None,
    }


def test_draft_case_id_is_null_without_catalog_ids(eval_dir):
    draft_cases(eval_dir)
    assert _load(eval_dir / "cases" / "toast.json")["id"] is None


def _header_case(tmp_path, checked_edit=None):
    (tmp_path / "inputs").mkdir()
    recipe = {"name": "Tart", "recipeIngredient": ["For the apples:", "2 apples, sliced"]}
    (tmp_path / "inputs" / "one.json").write_text(json.dumps(recipe))
    draft_cases(tmp_path)
    path = tmp_path / "cases" / "tart.json"
    _check(path, checked_edit)
    return path


def test_draft_writes_headers_without_ingredient_fields(tmp_path):
    path = _header_case(tmp_path)

    lines = _load(path)["expected"]["parsedIngredients"]
    assert lines[0] == {"raw": "For the apples:", "header": True, "group": "For the apples"}
    assert lines[1]["group"] == "For the apples"
    assert "header" not in lines[1]


def test_headers_score_on_group_name(tmp_path):
    _header_case(tmp_path)
    report = run_eval(tmp_path)
    assert (report.lines_correct, report.lines_total) == (2, 2)


def test_header_mismatches_are_reported(tmp_path):
    def treat_header_as_ingredient(expected):
        expected["parsedIngredients"][0] = {"raw": "For the apples:", "item": "apples"}

    _header_case(tmp_path, treat_header_as_ingredient)
    report = run_eval(tmp_path)

    assert report.lines_correct == 1
    assert report.mismatches[0].field == "header"


def test_draft_keeps_existing_cases(eval_dir):
    draft_cases(eval_dir)
    path = eval_dir / "cases" / "toast.json"
    _check(path)

    again = draft_cases(eval_dir)
    assert again.written == []
    assert again.already_drafted == 2
    assert _load(path)["checked"] is True


def test_draft_reads_complete_backup_and_drops_images(tmp_path):
    """The Export page's complete backup (/api/v1/export/all) nests recipe_data."""
    backup = {
        "export_type": "complete_backup",
        "user": {"email": "a@b.c"},
        "recipes": [
            {
                "id": 7,
                "name": "Soup",
                "description": "Warm",
                "source_url": "https://example.com/soup",
                "recipe_data": {
                    "recipeYield": "6 6 servings",
                    "recipeIngredient": ["2 cups stock"],
                    "images": [{"url": "x", "data": "A" * 1000, "mimeType": "image/jpeg"}],
                    "parsedIngredients": [{"raw": "2 cups stock", "parsedBy": "model"}],
                },
            },
            {"id": 8, "name": "Empty", "recipe_data": {}},
        ],
        "collections": [],
    }
    (tmp_path / "inputs").mkdir()
    (tmp_path / "inputs" / "complete_backup_2026-10-05.json").write_text(json.dumps(backup))

    result = draft_cases(tmp_path)

    assert [p.name for p in result.written] == ["soup.json"]
    case = _load(result.written[0])
    assert case["source"] == "inputs/complete_backup_2026-10-05.json#0"
    assert case["id"] == 7
    assert case["input"] == {
        "recipeYield": "6 6 servings",
        "recipeIngredient": ["2 cups stock"],
        "name": "Soup",
        "description": "Warm",
        "url": "https://example.com/soup",
    }
    assert case["expected"]["recipeYield"] == "6 servings"
    assert case["expected"]["parsedIngredients"][0]["item"] == "stock"


def test_draft_drops_schema_org_image_data(tmp_path):
    (tmp_path / "inputs").mkdir()
    recipe = {**RECIPES[1], "image": [{"url": "x", "data": "A" * 1000}]}
    (tmp_path / "inputs" / "one.json").write_text(json.dumps(recipe))

    result = draft_cases(tmp_path)

    assert "image" not in _load(result.written[0])["input"]


def _many_recipes(tmp_path, count=30):
    (tmp_path / "inputs").mkdir(parents=True)
    recipes = [{"name": f"Recipe {i}", "recipeIngredient": [f"{i} eggs"]} for i in range(count)]
    (tmp_path / "inputs" / "export.json").write_text(json.dumps(recipes))
    return tmp_path


def _drafted_sources(eval_dir):
    return {_load(p)["source"] for p in (eval_dir / "cases").glob("*.json")}


def test_draft_sample_is_repeatable(tmp_path):
    first = _many_recipes(tmp_path / "a")
    second = _many_recipes(tmp_path / "b")

    result = draft_cases(first, sample_size=5)
    draft_cases(second, sample_size=5)

    assert result.sampled == 5
    assert len(result.written) == 5
    assert result.recipes_found == 30
    assert _drafted_sources(first) == _drafted_sources(second)


def test_draft_sample_grows_without_dropping_earlier_picks(tmp_path):
    eval_dir = _many_recipes(tmp_path)
    draft_cases(eval_dir, sample_size=5)
    small = _drafted_sources(eval_dir)

    result = draft_cases(eval_dir, sample_size=8)

    assert result.already_drafted == 5
    assert len(result.written) == 3
    assert small < _drafted_sources(eval_dir)


def test_draft_sample_depends_on_seed(tmp_path):
    one = _many_recipes(tmp_path / "a")
    two = _many_recipes(tmp_path / "b")
    draft_cases(one, sample_size=5, seed=1)
    draft_cases(two, sample_size=5, seed=2)
    assert _drafted_sources(one) != _drafted_sources(two)


def test_draft_sample_larger_than_inputs_takes_all(tmp_path):
    eval_dir = _many_recipes(tmp_path, count=3)
    assert len(draft_cases(eval_dir, sample_size=40).written) == 3


def test_originals_match_case_names_and_omit_image_data(tmp_path):
    backup = {
        "recipes": [
            {
                "id": 7,
                "name": "Soup",
                "recipe_data": {
                    "recipeIngredient": ["2 cups stock"],
                    "images": [{"url": "u", "data": "A" * 5000, "mimeType": "image/jpeg"}],
                },
            },
            {"id": 8, "name": "Soup", "recipe_data": {"recipeIngredient": ["1 leek"]}},
        ]
    }
    (tmp_path / "inputs").mkdir()
    (tmp_path / "inputs" / "backup.json").write_text(json.dumps(backup))
    draft_cases(tmp_path)

    result = write_originals(tmp_path)

    assert result.written == 2
    assert result.missing == []
    names = sorted(p.name for p in (tmp_path / "originals").glob("*.json"))
    assert names == sorted(p.name for p in (tmp_path / "cases").glob("*.json"))
    assert names == ["soup-2.json", "soup.json"]

    first = _load(tmp_path / "originals" / "soup.json")
    assert first["id"] == 7
    assert first["recipe_data"]["images"][0] == {
        "url": "u",
        "data": "<5000 characters of image data omitted>",
        "mimeType": "image/jpeg",
    }
    assert _load(tmp_path / "originals" / "soup-2.json")["id"] == 8


def test_originals_report_cases_whose_source_is_gone(tmp_path):
    draft_dir = _many_recipes(tmp_path, count=2)
    draft_cases(draft_dir)
    (draft_dir / "inputs" / "export.json").write_text(json.dumps([RECIPES[0]]))
    (draft_dir / "cases" / "broken.json").write_text("{nope")

    result = write_originals(draft_dir)

    assert result.written == 1
    assert len(result.missing) == 2
    assert any("broken.json: not valid JSON" in m for m in result.missing)
    assert any("not found" in m for m in result.missing)


def test_draft_explains_why_nothing_was_found(tmp_path):
    assert draft_cases(tmp_path).warnings[0].startswith("No inputs folder")

    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (inputs / "notes.txt").write_text("hello")
    result = draft_cases(tmp_path)
    assert any("only .json files" in w for w in result.warnings)
    assert any("No .json files" in w for w in result.warnings)

    (inputs / "bad.json").write_text("{not json")
    (inputs / "collections.json").write_text(
        json.dumps({"collections": [{"name": "Dinners", "recipes": [{"id": 1, "name": "X"}]}]})
    )
    result = draft_cases(tmp_path)
    assert result.written == []
    assert any("bad.json: not valid JSON" in w for w in result.warnings)
    assert any("collections.json: no recipes with content" in w for w in result.warnings)


def test_run_scores_only_checked_cases(eval_dir):
    draft_cases(eval_dir)
    report = run_eval(eval_dir)

    assert report.unchecked_cases == 2
    assert report.lines_total == 0
    assert report.line_accuracy is None


def test_run_counts_lines_and_clean_recipes(eval_dir):
    draft_cases(eval_dir)

    def fix_lemon(expected):
        # The owner's hand-checked answer for the line the regex cannot parse
        expected["parsedIngredients"][2].update(quantity=1, item="lemon", note="juiced")

    _check(eval_dir / "cases" / "pancakes.json", fix_lemon)
    _check(eval_dir / "cases" / "toast.json")

    report = run_eval(eval_dir)

    assert (report.lines_correct, report.lines_total) == (3, 4)
    assert (report.recipes_clean, report.recipes_total) == (1, 2)
    assert report.line_accuracy == 0.75
    assert not report.meets_targets()
    assert [m.raw for m in report.mismatches] == ["Seeds scraped from 1 vanilla pod"]
    assert report.mismatches[0].field == "unparsed"

    text = format_report(report)
    assert "3/4 = 75.0%" in text
    assert "1/2 = 50.0%" in text
    assert "Seeds scraped from 1 vanilla pod" in text


def test_run_reports_yield_and_time_mismatches(eval_dir):
    draft_cases(eval_dir)
    _check(
        eval_dir / "cases" / "pancakes.json",
        lambda e: e.update(recipeYield="4 pancakes"),
    )

    report = run_eval(eval_dir)

    assert report.recipes_clean == 0
    assert report.mismatches[0].field == "recipeYield"


def test_ignored_lines_are_not_scored(eval_dir):
    draft_cases(eval_dir)
    _check(
        eval_dir / "cases" / "pancakes.json",
        lambda e: e["parsedIngredients"][2].update(ignore=True),
    )

    report = run_eval(eval_dir)

    assert (report.lines_correct, report.lines_total) == (2, 2)
    assert report.recipes_clean == 1


def test_lines_file_is_scored(tmp_path):
    (tmp_path / "lines.json").write_text(
        json.dumps(
            [
                {
                    "raw": "2 cups flour",
                    "expected": {"quantity": 2, "unit": "cup", "item": "flour"},
                },
                {"raw": "3 eggs", "expected": {"quantity": 3, "item": "EGGS "}},
                {
                    "raw": "1 tsp salt",
                    "expected": {"quantity": 2, "unit": "teaspoon", "item": "salt"},
                },
            ]
        )
    )

    report = run_eval(tmp_path)

    assert (report.lines_correct, report.lines_total) == (2, 3)
    assert report.recipes_total == 0
    assert report.mismatches[0].field == "quantity"


def test_eval_set_reports_targets():
    """
    Score the owner's eval set when it exists (design doc §8). Prints the two target
    numbers; fails below target only with INTAKE_EVAL_STRICT=1.

        INTAKE_EVAL_DIR=... uv run pytest tests/test_intake_eval.py -s -k eval_set
    """
    eval_dir = eval_dir_from_env()
    if not (eval_dir / "cases").exists() and not (eval_dir / "lines.json").exists():
        pytest.skip(f"No eval set at {eval_dir}")

    report = run_eval(eval_dir)
    print("\n" + format_report(report))

    if os.environ.get("INTAKE_EVAL_STRICT") == "1":
        assert report.line_accuracy is None or report.line_accuracy >= LINE_TARGET
        assert report.recipe_clean_rate is None or report.recipe_clean_rate >= RECIPE_TARGET
