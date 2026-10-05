"""
Eval harness for recipe cleanup (design doc §8).

Real recipes are other people's text, so the eval set lives outside git, in a
git-ignored folder (default `backend/eval-data/`, or `INTAKE_EVAL_DIR`):

    eval-data/
      inputs/     raw recipes as .json: the Export page's complete backup
                  (`/api/v1/export/all`), the recipes export
                  (`/api/v1/export/recipes?format=json`), a siphon download, or any
                  schema.org recipe or array of them. Image data is dropped.
      cases/      one file per recipe, written by `draft` and hand-checked by the owner
                  (`draft --sample N` drafts only a repeatable random sample)
      originals/  written by `originals`: each case's source record, same file name as
                  the case, image data omitted, for side-by-side comparison
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
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.services.recipe_cleanup import TIME_FIELDS, clean_recipe_data


LINE_TARGET = 0.95
RECIPE_TARGET = 0.90

DEFAULT_EVAL_DIR = Path(__file__).resolve().parents[2] / "eval-data"
DEFAULT_SAMPLE_SEED = 1
IMAGE_DATA_LIMIT = 200  # `data` strings longer than this are treated as image data
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


@dataclass
class InputScan:
    """What `_load_inputs` found, so `draft` can explain a result of zero."""

    files: int = 0
    recipes: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _recipe_from_item(item: Any) -> dict[str, Any] | None:
    """
    Turn one exported item into a schema.org recipe, or None if it has no recipe content.

    Accepts a schema.org recipe (recipes export, siphon download) and a catalog record
    with `recipe_data` (the "complete backup" from /api/v1/export/all). Image data and any
    stored `parsedIngredients` are dropped: images only bloat the case files, and the
    eval must parse from the raw lines.
    """
    if not isinstance(item, dict):
        return None
    if isinstance(item.get("recipe_data"), dict):
        recipe = {
            **item["recipe_data"],
            "name": item.get("name") or item["recipe_data"].get("name"),
            "description": item.get("description") or "",
            "url": item.get("source_url") or "",
        }
    else:
        recipe = dict(item)
    if not recipe.get("name") or not any(
        key in recipe for key in ("recipeIngredient", "recipeYield", *TIME_FIELDS)
    ):
        return None
    for key in ("image", "images", "parsedIngredients"):
        recipe.pop(key, None)
    return recipe


def _items_in_export(data: Any) -> list[Any]:
    """The recipe items in an export: an array, a "recipes" wrapper, or a single recipe."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("recipes"), list):
        return list(data["recipes"])
    return [data]


def _load_inputs(eval_dir: Path) -> InputScan:
    scan = InputScan()
    inputs_dir = eval_dir / "inputs"
    if not inputs_dir.is_dir():
        scan.warnings.append(f"No inputs folder: create {inputs_dir} and put export files in it")
        return scan

    for path in sorted(inputs_dir.iterdir()):
        if path.suffix.lower() != ".json":
            if path.is_file() and not path.name.startswith("."):
                scan.warnings.append(f"Skipped {path.name}: only .json files are read")
            continue
        scan.files += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            scan.warnings.append(f"Skipped {path.name}: not valid JSON ({e})")
            continue

        found = 0
        for index, item in enumerate(_items_in_export(data)):
            recipe = _recipe_from_item(item)
            if recipe is not None:
                scan.recipes.append((f"inputs/{path.name}#{index}", recipe))
                found += 1
        if not found:
            scan.warnings.append(
                f"{path.name}: no recipes with content found. Use the recipes export "
                "(JSON) or the complete backup; the collections export lists names only."
            )
    if scan.files == 0:
        scan.warnings.append(f"No .json files in {inputs_dir}")
    return scan


def _expected_from_output(data: dict[str, Any]) -> dict[str, Any]:
    expected: dict[str, Any] = {f: data[f] for f in RECIPE_FIELDS if data.get(f) not in (None, "")}
    expected["parsedIngredients"] = [
        {"raw": e["raw"], **{f: e.get(f) for f in COMPARED_FIELDS}}
        for e in data.get("parsedIngredients", [])
    ]
    return expected


@dataclass
class DraftResult:
    written: list[Path]
    input_files: int
    recipes_found: int
    already_drafted: int
    warnings: list[str]
    sampled: int | None = None


def _sample(
    recipes: list[tuple[str, dict[str, Any]]], size: int, seed: int
) -> list[tuple[str, dict[str, Any]]]:
    """
    A repeatable random sample. The whole list is shuffled with `seed` and the first
    `size` taken, so a larger size keeps every recipe a smaller one picked.
    """
    shuffled = sorted(recipes, key=lambda r: r[0])
    random.Random(seed).shuffle(shuffled)
    chosen = {source for source, _ in shuffled[:size]}
    return [r for r in recipes if r[0] in chosen]


def draft_cases(
    eval_dir: Path, sample_size: int | None = None, seed: int = DEFAULT_SAMPLE_SEED
) -> DraftResult:
    """
    Write a case for every input recipe that has none yet. Existing cases are kept.

    With `sample_size`, only a repeatable random sample of the input recipes is drafted
    (see `_sample`); the same size and seed always pick the same recipes.
    """
    cases_dir = eval_dir / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)
    existing_sources = set()
    for case_path in cases_dir.glob("*.json"):
        try:
            existing_sources.add(json.loads(case_path.read_text(encoding="utf-8")).get("source"))
        except json.JSONDecodeError:
            continue

    scan = _load_inputs(eval_dir)
    candidates = (
        _sample(scan.recipes, sample_size, seed) if sample_size is not None else scan.recipes
    )
    written: list[Path] = []
    already = 0
    for source, recipe in candidates:
        if source in existing_sources:
            already += 1
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
    return DraftResult(
        written=written,
        input_files=scan.files,
        recipes_found=len(scan.recipes),
        already_drafted=already,
        warnings=scan.warnings,
        sampled=len(candidates) if sample_size is not None else None,
    )


# ----------------------------------------------------------------------------
# Originals: each case's source record, for side-by-side comparison
# ----------------------------------------------------------------------------


def _omit_image_data(value: Any) -> Any:
    """Replace long base64 `data` strings (embedded images) with a short placeholder."""
    if isinstance(value, dict):
        return {
            key: (
                f"<{len(item)} characters of image data omitted>"
                if key == "data" and isinstance(item, str) and len(item) > IMAGE_DATA_LIMIT
                else _omit_image_data(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_omit_image_data(item) for item in value]
    return value


@dataclass
class OriginalsResult:
    written: int
    missing: list[str]


def write_originals(eval_dir: Path) -> OriginalsResult:
    """
    Write `originals/<case name>.json` for every case: the record exactly as it is in the
    input file (catalog fields included), with image data replaced by a placeholder.
    Files are rewritten each time, so they always match the current inputs.
    """
    out_dir = eval_dir / "originals"
    out_dir.mkdir(parents=True, exist_ok=True)
    exports: dict[str, list[Any]] = {}
    written = 0
    missing: list[str] = []

    for case_path in sorted((eval_dir / "cases").glob("*.json")):
        try:
            source = str(json.loads(case_path.read_text(encoding="utf-8")).get("source") or "")
        except json.JSONDecodeError:
            missing.append(f"{case_path.name}: not valid JSON")
            continue
        file_name, _, index_text = source.partition("#")
        if not file_name or not index_text.isdigit():
            missing.append(f"{case_path.name}: no usable source")
            continue

        if file_name not in exports:
            export_path = eval_dir / file_name
            try:
                exports[file_name] = _items_in_export(
                    json.loads(export_path.read_text(encoding="utf-8"))
                )
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                exports[file_name] = []
        items = exports[file_name]
        index = int(index_text)
        if index >= len(items):
            missing.append(f"{case_path.name}: {source} not found")
            continue

        (out_dir / case_path.name).write_text(
            json.dumps(_omit_image_data(items[index]), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written += 1
    return OriginalsResult(written=written, missing=missing)


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
