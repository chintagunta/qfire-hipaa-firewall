from pathlib import Path

import pytest
import yaml

from qfire.errors import RuleValidationError
from qfire.rules import load_rules


def _write(tmp_path: Path, name: str, doc: dict) -> Path:
    file = tmp_path / name
    file.write_text(yaml.safe_dump(doc))
    return file


def test_missing_required_field_raises_with_file_and_field(tmp_path: Path):
    file = _write(
        tmp_path,
        "bad_rule.yaml",
        {
            "id": "bad_rule",
            # missing "scope"
            "pipeline": [{"type": "pattern", "deny": ["x"]}],
            "exemplars": {"in_scope": ["hi"]},
        },
    )
    with pytest.raises(RuleValidationError) as exc_info:
        load_rules(file)
    assert exc_info.value.field == "scope"
    assert str(file) == exc_info.value.file


def test_unknown_detector_type_raises(tmp_path: Path):
    file = _write(
        tmp_path,
        "bad_type.yaml",
        {
            "id": "bad_type_rule",
            "scope": "x",
            "pipeline": [{"type": "not_a_real_type"}],
            "exemplars": {"in_scope": ["hi"]},
        },
    )
    with pytest.raises(RuleValidationError):
        load_rules(file)


def test_empty_pipeline_raises(tmp_path: Path):
    file = _write(
        tmp_path,
        "empty_pipeline.yaml",
        {"id": "x", "scope": "x", "pipeline": [], "exemplars": {"in_scope": ["hi"]}},
    )
    with pytest.raises(RuleValidationError):
        load_rules(file)
