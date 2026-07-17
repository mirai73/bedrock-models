"""Tests for scripts/diff_models.py"""

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "diff_models.py"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _run(old_path: Path, new_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(old_path), str(new_path)],
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_files(tmp_path):
    """Return a factory that writes two JSON files and runs the script."""
    old_file = tmp_path / "old.json"
    new_file = tmp_path / "new.json"

    def factory(old: dict, new: dict) -> subprocess.CompletedProcess:
        _write_json(old_file, old)
        _write_json(new_file, new)
        return _run(old_file, new_file)

    return factory


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNoChange:
    def test_identical_files_reports_no_differences(self, tmp_files):
        data = {"model.a:0": {"regions": ["us-east-1"]}}
        result = tmp_files(data, data)
        assert result.returncode == 0
        assert "No differences found." in result.stdout

    def test_empty_files_reports_no_differences(self, tmp_files):
        result = tmp_files({}, {})
        assert result.returncode == 0
        assert "No differences found." in result.stdout


class TestNewKey:
    def test_added_key_is_labelled_new(self, tmp_files):
        old = {"model.a:0": {"regions": ["us-east-1"]}}
        new = {
            "model.a:0": {"regions": ["us-east-1"]},
            "model.b:0": {"regions": ["eu-west-1"]},
        }
        result = tmp_files(old, new)
        assert result.returncode == 0
        assert "[NEW] model.b:0" in result.stdout

    def test_new_key_shows_its_value(self, tmp_files):
        old = {}
        new = {"model.x:0": {"inputModalities": ["TEXT"]}}
        result = tmp_files(old, new)
        assert "[NEW] model.x:0" in result.stdout
        assert "TEXT" in result.stdout

    def test_new_key_summary_count(self, tmp_files):
        old = {}
        new = {"model.x:0": {}, "model.y:0": {}}
        result = tmp_files(old, new)
        assert "2 added" in result.stdout


class TestRemovedKey:
    def test_removed_key_is_labelled_removed(self, tmp_files):
        old = {
            "model.a:0": {"regions": ["us-east-1"]},
            "model.b:0": {"regions": ["eu-west-1"]},
        }
        new = {"model.a:0": {"regions": ["us-east-1"]}}
        result = tmp_files(old, new)
        assert result.returncode == 0
        assert "[REMOVED] model.b:0" in result.stdout

    def test_removed_key_shows_its_value(self, tmp_files):
        old = {"model.gone:0": {"regions": ["ap-southeast-1"], "runtime_supported": True}}
        new = {}
        result = tmp_files(old, new)
        assert "[REMOVED] model.gone:0" in result.stdout
        assert "ap-southeast-1" in result.stdout

    def test_removed_key_summary_count(self, tmp_files):
        old = {"model.x:0": {}, "model.y:0": {}}
        new = {}
        result = tmp_files(old, new)
        assert "2 removed" in result.stdout


class TestChangedKey:
    def test_changed_key_is_labelled_changed(self, tmp_files):
        old = {"model.a:0": {"regions": ["us-east-1"]}}
        new = {"model.a:0": {"regions": ["us-east-1", "eu-west-1"]}}
        result = tmp_files(old, new)
        assert result.returncode == 0
        assert "[CHANGED] model.a:0" in result.stdout

    def test_changed_key_shows_previous_and_new(self, tmp_files):
        old = {"model.a:0": {"regions": ["us-east-1"]}}
        new = {"model.a:0": {"regions": ["us-east-1", "eu-west-1"]}}
        result = tmp_files(old, new)
        assert "Previous:" in result.stdout
        assert "New:" in result.stdout

    def test_changed_key_summary_count(self, tmp_files):
        old = {"model.a:0": {"v": 1}, "model.b:0": {"v": 2}}
        new = {"model.a:0": {"v": 9}, "model.b:0": {"v": 8}}
        result = tmp_files(old, new)
        assert "2 changed" in result.stdout

    def test_unchanged_key_not_reported(self, tmp_files):
        old = {"model.a:0": {"v": 1}, "model.b:0": {"v": 2}}
        new = {"model.a:0": {"v": 1}, "model.b:0": {"v": 99}}
        result = tmp_files(old, new)
        # model.a is unchanged — should NOT appear
        assert "model.a:0" not in result.stdout
        assert "[CHANGED] model.b:0" in result.stdout


class TestMixedChanges:
    def test_all_three_types_at_once(self, tmp_files):
        old = {
            "keep.same:0": {"v": 1},
            "will.change:0": {"regions": ["us-east-1"]},
            "will.remove:0": {"v": 3},
        }
        new = {
            "keep.same:0": {"v": 1},
            "will.change:0": {"regions": ["us-east-1", "eu-west-1"]},
            "brand.new:0": {"inputModalities": ["TEXT"]},
        }
        result = tmp_files(old, new)
        assert "[NEW] brand.new:0" in result.stdout
        assert "[REMOVED] will.remove:0" in result.stdout
        assert "[CHANGED] will.change:0" in result.stdout
        assert "keep.same:0" not in result.stdout
        assert "1 added" in result.stdout
        assert "1 removed" in result.stdout
        assert "1 changed" in result.stdout


class TestSummaryLine:
    def test_summary_shows_all_zero_counts_when_no_change(self, tmp_files):
        result = tmp_files({}, {})
        # When there's nothing to report we get the short message, not a summary line
        assert "No differences found." in result.stdout

    def test_summary_line_present_when_there_are_changes(self, tmp_files):
        old = {"a:0": {"v": 1}}
        new = {"b:0": {"v": 2}}
        result = tmp_files(old, new)
        assert "Summary:" in result.stdout


class TestErrorHandling:
    def test_missing_file_exits_nonzero(self, tmp_path):
        old_file = tmp_path / "old.json"
        _write_json(old_file, {})
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(old_file), str(tmp_path / "nonexistent.json")],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_wrong_arg_count_exits_nonzero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Usage:" in result.stderr
