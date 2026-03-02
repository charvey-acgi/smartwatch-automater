import pytest
import shutil
from pathlib import Path
from smartwatch.config import Action, ActionType
from smartwatch.handlers import execute_action


@pytest.fixture
def tmp_src(tmp_path):
    """Create a temp source file."""
    src = tmp_path / "test.csv"
    src.write_text("a,b,c")
    return src


def test_copy_handler(tmp_path, tmp_src):
    dest_dir = tmp_path / "backup"
    action = Action(type=ActionType.copy, destination=str(dest_dir))

    execute_action(action, str(tmp_src), dry_run=False)

    assert (dest_dir / "test.csv").exists()
    assert (dest_dir / "test.csv").read_text() == "a,b,c"


def test_copy_handler_dry_run(tmp_path, tmp_src):
    dest_dir = tmp_path / "backup"
    action = Action(type=ActionType.copy, destination=str(dest_dir))

    execute_action(action, str(tmp_src), dry_run=True)

    assert not dest_dir.exists()  # nothing created in dry run ✅


def test_move_handler(tmp_path, tmp_src):
    dest_dir = tmp_path / "archive"
    action = Action(type=ActionType.move, destination=str(dest_dir))

    execute_action(action, str(tmp_src), dry_run=False)

    assert (dest_dir / "test.csv").exists()
    assert not tmp_src.exists()  # source removed ✅


def test_log_handler_doesnt_crash(tmp_src):
    action = Action(type=ActionType.log)
    execute_action(action, str(tmp_src), dry_run=False)  # just shouldn't raise