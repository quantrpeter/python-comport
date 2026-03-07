# python-comport

An interactive serial COM port terminal for the command line.

- Arrow-key menu to select the port
- Remembers your last port and baud rate — just press Enter to reconnect
- Works on Linux, macOS, and Windows
- No extra dependencies beyond `pyserial`

# Dev

press F5 in vscode


## Installation

```bash
pip install python-comport
```

## Usage

```bash
python-comport
```

1. Use `↑ ↓` to select a COM port and press **Enter**
2. Enter a baud rate (or press **Enter** to use the last saved value, default 9600)
3. Type messages and press **Enter** to send
4. Type `exit` or press **Ctrl+C** to quit

Settings are saved to `~/.comport-settings.json` so your last port and baud rate are pre-selected on the next run.

# Publish to pypi

```
pip install build twine
python -m build
twine upload dist/*
```

## Requirements

- Python 3.7+
- pyserial

## License

MIT
