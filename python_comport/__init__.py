import json
import os
import sys
import threading
import time

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("Error: 'pyserial' library is required but not installed.")
    print("    pip install pyserial")
    sys.exit(1)

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".comport-settings.json")


def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(port, baudrate):
    with open(SETTINGS_FILE, "w") as f:
        json.dump({"port": port, "baudrate": baudrate}, f)


def get_key():
    """Cross-platform function to detect arrow keys and Enter."""
    if os.name == 'nt':
        import msvcrt
        key = msvcrt.getch()
        if key in (b'\r', b'\n'):
            return 'enter'
        elif key == b'\xe0':
            key2 = msvcrt.getch()
            if key2 == b'H':
                return 'up'
            elif key2 == b'P':
                return 'down'
        return None
    else:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A':
                        return 'up'
                    elif ch3 == 'B':
                        return 'down'
            elif ch in ('\r', '\n'):
                return 'enter'
            return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


class SimpleMenu:
    """Simple arrow-key menu (no extra dependencies)."""

    def __init__(self, options, default=0):
        self.options = options
        self.selected = default

    def display(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=== Select COM Port ===")
        print("Use ↑ ↓ arrow keys to move, press Enter to select.")
        print("(cursor pre-set to last used port)\n")
        for i, option in enumerate(self.options):
            prefix = "→ " if i == self.selected else "  "
            print(f"{prefix}{option}")

    def run(self):
        while True:
            self.display()
            key = get_key()
            if key == 'up':
                self.selected = (self.selected - 1) % len(self.options)
            elif key == 'down':
                self.selected = (self.selected + 1) % len(self.options)
            elif key == 'enter':
                return self.selected


def main():
    settings = load_settings()

    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No COM ports found on your system.")
        sys.exit(1)

    ports = [p for p in ports if p.description and p.description.lower() != 'n/a']
    if not ports:
        print("No COM ports with valid descriptions found.")
        sys.exit(1)

    options = [f"{p.device}  —  {p.description}" for p in ports]

    saved_port = settings.get("port")
    default_idx = next((i for i, p in enumerate(ports) if p.device == saved_port), 0)

    menu = SimpleMenu(options, default=default_idx)
    selected_idx = menu.run()

    selected_port = ports[selected_idx].device

    saved_baud = settings.get("baudrate", 9600)
    baud_input = input(f"\nEnter baud rate for {selected_port} (default {saved_baud}): ").strip()
    try:
        baudrate = int(baud_input) if baud_input else saved_baud
    except ValueError:
        print(f"Invalid baud rate → using {saved_baud}")
        baudrate = saved_baud

    save_settings(selected_port, baudrate)

    try:
        ser = serial.Serial(
            port=selected_port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )
        print(f"\n✅ Connected to {selected_port} @ {baudrate} baud")
    except Exception as e:
        print(f"❌ Failed to open {selected_port}: {e}")
        sys.exit(1)

    def serial_reader():
        while ser.is_open:
            try:
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting).decode('utf-8', errors='replace')
                    if data:
                        print(data, end='', flush=True)
            except Exception:
                break
            time.sleep(0.01)

    threading.Thread(target=serial_reader, daemon=True).start()

    print("\n=== Serial Terminal Ready ===")
    print("• Type your message and press Enter to send")
    print("• Type 'exit' (or Ctrl+C) to quit\n")

    try:
        while True:
            cmd = input()
            if cmd.strip().lower() in ("exit", "quit"):
                break
            ser.write((cmd + '\r\n').encode('utf-8'))
            ser.flush()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    finally:
        if ser.is_open:
            ser.close()
        print("Serial port closed. Goodbye!")
