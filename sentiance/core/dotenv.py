"""A tiny, dependency-free ``.env`` loader.

`Settings` already reads `.env` for its own `SENTIANCE_*` variables, but other
tools read the raw environment — notably `HF_TOKEN`, which `transformers` /
`huggingface_hub` look for when downloading a base model. This loads every
`KEY=VALUE` line from a `.env` file into ``os.environ`` so those tools see it too.

It never overrides a variable already set in the real environment (so an explicit
``set HF_TOKEN=…`` wins), ignores comments and blank lines, and strips optional
surrounding quotes. No third-party dependency, so it runs anywhere.
"""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: str | Path = ".env") -> int:
    """Load ``KEY=VALUE`` pairs from ``path`` into ``os.environ`` (without
    overriding existing vars). Returns how many new keys were set; 0 if the file
    is absent. Silent and safe to call unconditionally at startup."""
    p = Path(path)
    if not p.exists():
        return 0
    set_count = 0
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        # drop an optional leading "export ", strip matching surrounding quotes
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value
            set_count += 1
    return set_count
