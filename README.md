# smartwatch-automator

A configurable file watcher and automator for Windows, Mac and Linux.
Watch directories and automatically trigger actions (copy, move, run scripts)
when files change.

## Installation
```bash
pip install smartwatch-automator
```

## Quick Start

Create a `config.yaml`:
```yaml
watch:
  - path: "/your/directory"
    recursive: true
    rules:
      - name: "Backup CSVs"
        patterns: ["*.csv"]
        on_events: ["created", "modified"]
        action:
          type: copy
          destination: "/your/backup"
```

Then run:
```bash
smartwatch --config config.yaml --verbose
```

## Actions

| Action | Description |
|--------|-------------|
| `log`  | Log file events to console |
| `copy` | Copy file to destination |
| `move` | Move file to destination |
| `run`  | Run a shell command (`{file}` = file path) |

## Options
```
--config    Path to config YAML (default: config.yaml)
--dry-run   Preview actions without executing
--verbose   Show debug output
```

## License
MIT