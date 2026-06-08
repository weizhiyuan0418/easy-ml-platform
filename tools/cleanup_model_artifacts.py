from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Find or delete orphan Easy ML Platform model artifacts.")
    parser.add_argument("--delete", action="store_true", help="Delete orphan files. Omit for dry-run output only.")
    args = parser.parse_args()

    django.setup()
    from mlapp.services import cleanup_orphan_model_artifacts  # noqa: E402

    result = cleanup_orphan_model_artifacts(delete=args.delete)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
