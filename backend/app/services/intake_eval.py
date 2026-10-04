"""
Eval harness for recipe cleanup (design doc §8).

Real recipes are other people's text, so the eval set lives outside git, in a
git-ignored folder (default `backend/eval-data/`, or `INTAKE_EVAL_DIR`):

    eval-data/
      inputs/     raw recipes as JSON: one schema.org object or an array, such as a
                  catalog export (`/api/v1/export/recipes?format=json`)
      cases/      one file per recipe, written by `draft` and hand-checked by the owner
      lines.json  optional extra ingredient lines: [{"raw": ..., "expected": {...}}]
      pages/      failing pages saved as text, for phase 4 extraction; not read here

A case file looks like:

    {
      "checked": false,
      "source": "inputs/export.json#3",
      "input": { ...schema.org recipe... },
      "expected": {
        "recipeYield": "4 servings",
        "prepTime": "PT15M",
        "parsedIngredients": [
          {"quantity": 2, "quantityMax": null, "unit": "cup", "item": "flour",
           "note": "sifted", "group": null},
          ...
        ]
      }
    }

`draft` fills `expected` with the current output. The owner corrects it, sets
`"checked": true`, and only checked cases are scored. An expected ingredient entry with
`"ignore": true` is left out of the score.

`run` reports the two targets: the share of ingredient lines parsed correctly (95%) and
the share of recipes needing no edits, meaning yield, times and every ingredient line
match (90%).
"""

import json
import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.services.recipe_cleanup import TIME_FIELDS, clean_recipe_data


LINE_TARGET = 0.95
RECIPE_TARGET = 0.90

DEFAULT_EVAL_DIR = Path(__file__).resolve().parents[2] / "eval-data"
COMPARED_FIELDS = ("quantity", "quantityMax", "unit", "item", "note", "group")
RECIPE_FIELDS = ("recipeYield", *TIME_FIELDS)


def eval_dir_from_env() -> Path:
    return Path(os.environ.get("INTAKE_EVAL_DIR") or DEFAULT_EVAL_DIR)


@dataclass
class Mismatch:
    case: str
    field: str
    raw: str | None
    expected: Any
    actual: Any


@dataclass
class EvalReport:
    lines_total: int = 0
    lines_correct: int = 0
    recipes_total: int = 0
    recipes_clean: int = 0
    unchecked_cases: int = 0
    mismatches: list[Mismatch] = field(default_factory=list)

    @property
    def line_accuracy(self) -> float | None:
        return self.lines_correct / self.lines_total if self.lines_total else None

    @property
    def recipe_clean_rate(self) -> float | None:
        return self.recipes_clean / self.recipes_total if self.recipes_total else None

    def meets_targets(self) -> bool:
        line = self.line_accuracy
        recipe = self.recipe_clean_rate
        return (line is None or line >= LINE_TARGET) and (recipe is None or recipe >= RECIPE_TARGET)


# ----------------------------------------------------------------------------
# Drafting cases
# ----------------------------------------------------------------------------


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or "recipe"


def _load_inputs(eval_dir: Path) -> list[tuple[str, dict[str, Any]]]:
    recipes: list[tuple[str, dict[str, Any]]] = []
    for path in sorted((eval_dir / "inputs").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else [data]
        for index, item in enumerate(items):
            if isinstance(item, dict) and item.get("name"):
                recipes.append((f"inputs/{path.name}#{index}", item))
    return recipes


def _expected_from_output(data: dict[str, Any]) -> dict[str, Any]:
    expected: dict[str, Any] = {f: data[f] for f in RECIPE_FIELDS if data.get(f) not in (None, "")}
    expected["parsedIngredients"] = [
        {"raw": e["raw"], **{f: e.get(f) for f in COMPARED_FIELDS}}
        for e in data.get("parsedIngredients", [])
    ]
    return expected


def draft_cases(eval_dir: Path) -> list[Path]:
    """Write a case for every input recipe that has none yet. Existing cases are kept."""
    cases_dir = eval_dir / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)
    existing_sources = set()
    for case_path in cases_dir.glob("*.json"):
        try:
            existing_sources.add(json.loads(case_path.read_text(encoding="utf-8")).get("source"))
        except json.JSONDecodeError:
            continue

    written: list[Path] = []
    for source, recipe in _load_inputs(eval_dir):
        if source in existing_sources:
            continue
        base = _slug(str(recipe.get("name")))
        path = cases_dir / f"{base}.json"
        suffix = 2
        while path.exists():
            path = cases_dir / f"{base}-{suffix}.json"
            suffix += 1
        result = clean_recipe_data(recipe)
        case = {
            "checked": False,
            "source": source,
            "input": recipe,
            "expected": _expected_from_output(result.data),
        }
        path.write_text(json.dumps(case, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(path)
    return written


# ----------------------------------------------------------------------------
# Scoring
# ----------------------------------------------------------------------------


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        text = re.sub(r"\s+", " ", value).strip().casefold()
        return text or None
    return value


def _values_match(expected: Any, actual: Any) -> bool:
    if isinstance(expected, int | float) and isinstance(actual, int | float):
        return math.isclose(float(expected), float(actual), abs_tol=0.01)
    return bool(_normalize(expected) == _normalize(actual))


def _line_matches(expected: dict[str, Any], actual: dict[str, Any] | None) -> list[str]:
    """Return the names of fields that differ (empty when the line is correct)."""
    if actual is None:
        return ["missing"]
    is_header = expected.get("item") is None and expected.get("group") is not None
    if not is_header and actual.get("parsedBy") is None:
        return ["unparsed"]
    return [f for f in COMPARED_FIELDS if not _values_match(expected.get(f), actual.get(f))]


def _score_lines(
    report: EvalReport,
    case_name: str,
    expected_lines: list[dict[str, Any]],
    actual_lines: list[dict[str, Any]],
) -> bool:
    all_correct = True
    for index, expected in enumerate(expected_lines):
        if expected.get("ignore"):
            continue
        actual = actual_lines[index] if index < len(actual_lines) else None
        raw = expected.get("raw") or (actual or {}).get("raw")
        if not str(raw or "").strip():
            continue
        report.lines_total += 1
        differing = _line_matches(expected, actual)
        if differing:
            all_correct = False
            report.mismatches.append(
                Mismatch(
                    case=case_name,
                    field=",".join(differing),
                    raw=raw,
                    expected={f: expected.get(f) for f in COMPARED_FIELDS},
                    actual=(
                        {f: actual.get(f) for f in (*COMPARED_FIELDS, "parsedBy")}
                        if actual
                        else None
                    ),
                )
            )
        else:
            report.lines_correct += 1
    return all_correct


def run_eval(eval_dir: Path) -> EvalReport:
    """Score every checked case (and `lines.json`) against current cleanup output."""
    report = EvalReport()

    for case_path in sorted((eval_dir / "cases").glob("*.json")):
        case = json.loads(case_path.read_text(encoding="utf-8"))
        if not case.get("checked"):
            report.unchecked_cases += 1
            continue

        expected = case.get("expected") or {}
        result = clean_recipe_data(case.get("input") or {})
        recipe_ok = True

        for recipe_field in RECIPE_FIELDS:
            if recipe_field in expected and not _values_match(
                expected[recipe_field], result.data.get(recipe_field)
            ):
                recipe_ok = False
                report.mismatches.append(
                    Mismatch(
                        case=case_path.stem,
                        field=recipe_field,
                        raw=None,
                        expected=expected[recipe_field],
                        actual=result.data.get(recipe_field),
                    )
                )

        lines_ok = _score_lines(
            report,
            case_path.stem,
            expected.get("parsedIngredients") or [],
            result.data.get("parsedIngredients") or [],
        )
        report.recipes_total += 1
        if recipe_ok and lines_ok:
            report.recipes_clean += 1

    lines_file = eval_dir / "lines.json"
    if lines_file.exists():
        cases = json.loads(lines_file.read_text(encoding="utf-8"))
        raws = [c["raw"] for c in cases]
        actual = clean_recipe_data({"recipeIngredient": raws}).data["parsedIngredients"]
        _score_lines(
            report,
            "lines.json",
            [{"raw": c["raw"], **c.get("expected", {})} for c in cases],
            actual,
        )

    return report


def _percent(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1%}"


def format_report(report: EvalReport, show: int = 20) -> str:
    lines = [
        "Recipe cleanup eval",
        f"  Ingredient lines parsed correctly: {report.lines_correct}/{report.lines_total}"
        f" = {_percent(report.line_accuracy)} (target {LINE_TARGET:.0%})",
        f"  Recipes needing no edits:          {report.recipes_clean}/{report.recipes_total}"
        f" = {_percent(report.recipe_clean_rate)} (target {RECIPE_TARGET:.0%})",
    ]
    if report.unchecked_cases:
        lines.append(f"  Unchecked cases (not scored):      {report.unchecked_cases}")
    if report.mismatches:
        lines.append("")
        lines.append(f"Mismatches (first {min(show, len(report.mismatches))}):")
        for m in report.mismatches[:show]:
            where = f"{m.case}: {m.raw!r}" if m.raw is not None else f"{m.case}: {m.field}"
            lines.append(f"  - {where} [{m.field}]")
            lines.append(f"      expected {json.dumps(m.expected, ensure_ascii=False)}")
            lines.append(f"      actual   {json.dumps(m.actual, ensure_ascii=False)}")
    return "\n".join(lines)
