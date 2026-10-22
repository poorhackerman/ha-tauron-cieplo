"""Fill HACS repository metadata: python configure_repository.py OWNER/REPO."""

import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 2 or not re.fullmatch(
    r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+", sys.argv[1]
):
    raise SystemExit("Usage: python configure_repository.py OWNER/REPO")
repo = sys.argv[1]
path = Path(__file__).parent / "custom_components/tauron_cieplo/manifest.json"
manifest = json.loads(path.read_text(encoding="utf-8"))
manifest.update(
    documentation=f"https://github.com/{repo}",
    issue_tracker=f"https://github.com/{repo}/issues",
    codeowners=[f"@{repo.split('/')[0]}"],
)
path.write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"Configured repository: {repo}")
