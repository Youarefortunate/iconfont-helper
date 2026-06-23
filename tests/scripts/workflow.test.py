import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from workflow import resolve_project_root, resolve_project_path


def test_resolve_project_root_uses_configured_project_root():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        result = resolve_project_root({"project_root": str(root)})

        assert result == root.resolve()


def test_resolve_project_root_uses_environment_root_when_config_is_empty():
    old_value = os.environ.get("ICONFONT_PROJECT_ROOT")
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["ICONFONT_PROJECT_ROOT"] = temp_dir
        try:
            result = resolve_project_root({})
        finally:
            if old_value is None:
                os.environ.pop("ICONFONT_PROJECT_ROOT", None)
            else:
                os.environ["ICONFONT_PROJECT_ROOT"] = old_value

        assert result == Path(temp_dir).resolve()


def test_resolve_project_root_falls_back_to_current_working_directory():
    old_cwd = Path.cwd()
    old_value = os.environ.pop("ICONFONT_PROJECT_ROOT", None)
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        try:
            result = resolve_project_root({})
        finally:
            os.chdir(old_cwd)
            if old_value is not None:
                os.environ["ICONFONT_PROJECT_ROOT"] = old_value

        assert result == Path(temp_dir).resolve()


def test_resolve_project_path_keeps_absolute_path():
    with tempfile.TemporaryDirectory() as temp_dir:
        target = Path(temp_dir) / "icons"
        result = resolve_project_path(Path.cwd(), str(target))

        assert result == target.resolve()


def test_resolve_project_path_joins_relative_path_with_project_root():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        result = resolve_project_path(root, "assets/icons")

        assert result == root.resolve() / "assets" / "icons"
