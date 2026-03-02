import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from smartwatch.config import Rule, EventType
from smartwatch.handlers import execute_action
from smartwatch.debouncer import Debouncer

logger = logging.getLogger(__name__)


class SmartHandler(FileSystemEventHandler):
    def __init__(self, rules: list[Rule], dry_run: bool = False, debounce_wait: float = 0.5):
        self.rules = rules
        self.dry_run = dry_run
        self.debouncer = Debouncer(wait=debounce_wait)

    def _get_matching_rules(self, path: str, event_type: EventType) -> list[Rule]:
        return [
            rule for rule in self.rules
            if event_type in rule.on_events
            and any(Path(path).match(p) for p in rule.patterns)
            and not self._is_in_destination(path, rule)
        ]

    def _is_in_destination(self, path: str, rule: Rule) -> bool:
        if rule.action.destination:
            dest = Path(rule.action.destination).resolve()
            try:
                Path(path).resolve().relative_to(dest)
                return True
            except ValueError:
                return False
        return False

    def _dispatch(self, path: str, event_type: EventType):
        try:
            logger.debug(f"Evaluating path: {path} | event: {event_type}")
            for rule in self._get_matching_rules(path, event_type):
                logger.debug(f"Rule '{rule.name}' matched {path}")
                # Use file path as debounce key — collapses all events for same file
                debounce_key = f"{rule.name}:{path}"
                self.debouncer.call(
                    debounce_key,
                    execute_action,
                    rule.action, path, self.dry_run
                )
        except Exception as e:
            logger.error(f"Error dispatching {path}: {e}", exc_info=True)

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            self._dispatch(event.src_path, EventType.created)

    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory:
            self._dispatch(event.src_path, EventType.modified)

    def on_deleted(self, event: FileSystemEvent):
        if not event.is_directory:
            self._dispatch(event.src_path, EventType.deleted)

    def on_moved(self, event: FileSystemEvent):
        if not event.is_directory:
            self._dispatch(event.dest_path, EventType.moved)

    def stop(self):
        """Clean up debouncer timers on shutdown."""
        self.debouncer.cancel_all()


def start_watcher(path: str, handler: SmartHandler, recursive: bool = True) -> Observer:
    observer = Observer()
    observer.schedule(handler, path=path, recursive=recursive)
    observer.start()
    logger.info(f"Watching: {path} (recursive={recursive})")
    return observer