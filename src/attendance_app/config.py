from pathlib import Path

# Directory on local filesystem synchronized with Google Drive
NOTIFICATION_DIR = Path('notifications')

# History file location
HISTORY_FILE = Path('print_history.json')

# Brother P-touch Editor executable path
PTOUCH_EDITOR = r"C:\Program Files (x86)\Brother P-touch Editor\Ptedit.exe"

# Label template file used by P-touch Editor
LABEL_TEMPLATE = Path('label_template.lbx')

import json

from pathlib import Path

# Settings storage shared with the root application
# Located two directories above this file (project root)
SETTINGS_FILE = Path(__file__).resolve().parents[2] / 'settings.json'


def load_settings() -> dict:
    """Load settings for the attendance app."""
    if SETTINGS_FILE.exists():
        try:
            with SETTINGS_FILE.open('r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}


def save_settings(data: dict) -> None:
    """Persist settings for the attendance app."""
    # GAS連携を無効化したため、gas_webapp_urlの設定は削除
    SETTINGS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8'
    )