"""Tamper-evident append-only audit log.

This uses a simple hash chain across JSONL records:
- each entry includes `prev_hash`
- the entry's `entry_hash` is SHA-256(prev_hash + canonical_json(entry_without_entry_hash))

It is not a full WORM store, but it provides strong tamper evidence for
accidental/moderate malicious edits of audit history.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True)
class AuditAppendResult:
    entry_hash: str
    prev_hash: str


class TamperEvidentAuditLog:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def _ensure_parent_dir(self) -> None:
        parent = os.path.dirname(self.file_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def _read_last_hash(self) -> str:
        if not os.path.exists(self.file_path):
            return "0" * 64

        # Read last non-empty line
        with open(self.file_path, "rb") as f:
            try:
                f.seek(-2, os.SEEK_END)
                while f.tell() > 0:
                    ch = f.read(1)
                    if ch == b"\n":
                        break
                    f.seek(-2, os.SEEK_CUR)
            except OSError:
                # small file
                f.seek(0)

            last_line = f.readline().decode("utf-8", errors="replace").strip()

        if not last_line:
            return "0" * 64

        try:
            obj = json.loads(last_line)
            entry_hash = obj.get("entry_hash")
            if isinstance(entry_hash, str) and len(entry_hash) == 64:
                return entry_hash
        except Exception:
            return "0" * 64

        return "0" * 64

    def append(self, entry: Dict[str, Any]) -> AuditAppendResult:
        """Append an entry and return hashes."""
        self._ensure_parent_dir()

        prev_hash = self._read_last_hash()

        base: Dict[str, Any] = {
            "timestamp": _utc_now_iso(),
            **entry,
            "prev_hash": prev_hash,
        }

        payload = _canonical_json(base)
        entry_hash = _sha256_hex((prev_hash + payload).encode("utf-8"))

        record = {**base, "entry_hash": entry_hash}
        line = json.dumps(record, separators=(",", ":"), default=str)

        # Best-effort atomic append
        with open(self.file_path, "a", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")

        return AuditAppendResult(entry_hash=entry_hash, prev_hash=prev_hash)

    def verify_chain(self, max_lines: Optional[int] = None) -> Dict[str, Any]:
        """Verify the hash chain integrity.

        Returns a dict: {"ok": bool, "checked": int, "broken_at": int|None}
        """
        if not os.path.exists(self.file_path):
            return {"ok": True, "checked": 0, "broken_at": None}

        prev_hash = "0" * 64
        checked = 0

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if max_lines is not None and checked >= max_lines:
                    break

                line = line.strip()
                if not line:
                    continue

                obj = json.loads(line)
                entry_hash = obj.get("entry_hash")
                stored_prev = obj.get("prev_hash")

                if stored_prev != prev_hash:
                    return {"ok": False, "checked": checked, "broken_at": checked + 1}

                obj_wo_hash = dict(obj)
                obj_wo_hash.pop("entry_hash", None)

                payload = _canonical_json(obj_wo_hash)
                computed = _sha256_hex((prev_hash + payload).encode("utf-8"))
                if computed != entry_hash:
                    return {"ok": False, "checked": checked, "broken_at": checked + 1}

                prev_hash = entry_hash
                checked += 1

        return {"ok": True, "checked": checked, "broken_at": None}
