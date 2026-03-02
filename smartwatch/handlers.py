import logging
import time
import shutil
import subprocess
from pathlib import Path
from smartwatch.config import Action, ActionType

logger = logging.getLogger(__name__)


def execute_action(action: Action, file_path: str, dry_run: bool = False):
    """Route to the correct handler based on action type."""
    handlers = {
        ActionType.log:  _handle_log,
        ActionType.copy: _handle_copy,
        ActionType.move: _handle_move,
        ActionType.run:  _handle_run,
    }
    handler = handlers.get(action.type)
    if handler:
        handler(action, file_path, dry_run)
    else:
        logger.warning(f"Unknown action type: {action.type}")


def _handle_log(action: Action, file_path: str, dry_run: bool):
    logger.info(f"[LOG] File event on: {file_path}")


def _handle_copy(action: Action, file_path: str, dry_run: bool):
    src = Path(file_path)
    dest = Path(action.destination) / src.name

    if dry_run:
        logger.info(f"[DRY-RUN] Would copy {src} → {dest}")
        return

    dest.parent.mkdir(parents=True, exist_ok=True)

    # Retry loop — wait for Windows to release the file lock
    for attempt in range(5):
        try:
            shutil.copy2(src, dest)
            logger.info(f"[COPY] {src} → {dest}")
            return
        except PermissionError:
            logger.debug(f"File locked, retrying ({attempt + 1}/5)...")
            time.sleep(0.5)

    logger.error(f"[COPY] Failed after 5 attempts: {src}")


def _handle_move(action: Action, file_path: str, dry_run: bool):
    src = Path(file_path)
    dest = Path(action.destination) / src.name

    if dry_run:
        logger.info(f"[DRY-RUN] Would move {src} → {dest}")
        return

    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Try atomic rename first (same drive — instant, no copy)
        src.rename(dest)
        logger.info(f"[MOVE] {src} → {dest}")
    except OSError:
        # Falls back to copy+delete if rename fails (cross-drive move)
        shutil.copy2(src, dest)
        src.unlink()  # ✅ explicitly delete source
        logger.info(f"[MOVE] {src} → {dest} (copy+delete fallback)")


def _handle_run(action: Action, file_path: str, dry_run: bool):
    cmd = action.command.replace("{file}", file_path)

    if dry_run:
        logger.info(f"[DRY-RUN] Would run: {cmd}")
        return

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        logger.info(f"[RUN] {cmd} → exit code {result.returncode}")
        if result.stdout:
            logger.debug(f"stdout: {result.stdout.strip()}")
        if result.stderr:
            logger.warning(f"stderr: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        logger.error(f"[RUN] Command timed out: {cmd}")