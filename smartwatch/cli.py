import signal
import logging
import typer
import threading
from smartwatch.config import load_config
from smartwatch.watcher import SmartHandler, start_watcher


app = typer.Typer()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


@app.command()
def watch(
    config_path: str = typer.Option("config.yaml", "--config", "-c", help="Path to config YAML"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Log actions without executing them"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose mode"),
):
    stop_event = threading.Event()
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = load_config(config_path)
    observers = []

    for watch_config in config.watch:
        handler = SmartHandler(rules=watch_config.rules, dry_run=dry_run)
        observer = start_watcher(watch_config.path, handler, watch_config.recursive)
        observers.append(observer)

    def shutdown(sig, frame):
        typer.echo("\nShutting down...")
        for obs in observers:
            obs.stop()
        stop_event.set()  # ✅ unblocks main thread

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    while not stop_event.is_set():
        stop_event.wait(timeout=1)

    stop_event.wait()  # ✅ replaces observer.join() — responds to Ctrl+C properly

    for obs in observers:
        obs.join()

    typer.echo("Watch complete!")
