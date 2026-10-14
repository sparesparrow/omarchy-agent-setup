#!/usr/bin/env python3
"""Fail-closed local intake gate; not an agent sandbox or proof of safe content."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import unicodedata

MAX_BYTES = 1_000_000
PROVIDERS = {"perplexity", "gemini"}
PATTERNS = (
    r"\b(ignore|disregard|override)\b.{0,100}\b(instructions?|system|developer)\b",
    r"<\|?(system|developer|assistant|im_start)\b",
    r"\b(run|execute)\b.{0,60}\b(shell|bash|command|terminal)\b",
    r"\b(send|upload|exfiltrate|reveal)\b.{0,100}\b(secrets?|tokens?|credentials?|passwords?|keys?)\b",
    r"\b(curl|wget|sudo)\s|\brm\s+-[a-z]*[rf]",
)


def job_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
        raise ValueError("invalid job_id")
    return value


@contextmanager
def directory(repo, *parts):
    """Open each fixed component without following symlinks (Linux openat)."""
    fd = os.open(Path(repo).resolve(strict=True), os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts:
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", part) or part in {".", ".."}:
                raise ValueError("invalid directory component")
            try:
                os.mkdir(part, mode=0o700, dir_fd=fd)
            except FileExistsError:
                pass
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        yield fd
    finally:
        os.close(fd)


def write_new(fd, name, data):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or name in {".", ".."}:
        raise ValueError("invalid filename")
    out = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
    with os.fdopen(out, "wb") as stream:
        stream.write(data)


def read_report(fd, name):
    source = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    with os.fdopen(source, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("report must be a regular, non-hardlinked file")
        if info.st_size > MAX_BYTES:
            raise ValueError("report exceeds size limit")
        data = stream.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("report exceeds size limit")
    return data


def screen(data):
    text = data.decode("utf-8", errors="strict")
    if not text.strip():
        raise ValueError("empty report")
    if any(unicodedata.category(c) in {"Cc", "Cf", "Cs"} and c not in "\n\r\t" for c in text):
        raise ValueError("control or hidden-format characters")
    normalized = unicodedata.normalize("NFKC", text)
    if any(re.search(pattern, normalized, re.I | re.S) for pattern in PATTERNS):
        raise ValueError("known instruction/tool/secret-access pattern")
    return text


def intake(repo, job, provider, approval=None):
    job_id(job)
    if provider not in PROVIDERS:
        raise ValueError("unknown provider")
    with directory(repo, ".agents", "research", "inbox", job) as fd:
        data = read_report(fd, f"{provider}-report.md")
    digest = hashlib.sha256(data).hexdigest()
    result = {"job_id": job, "provider": provider, "sha256": digest,
              "trust": "untrusted", "status": "QUARANTINED"}
    try:
        text = screen(data)
    except (ValueError, UnicodeError) as error:
        result["reason"] = str(error)
        return result
    result["status"] = "NEEDS_REVIEW"
    if approval is None:
        return result
    if approval != digest:
        raise ValueError("approval digest does not match the exact report bytes")
    payload = {**result, "status": "REVIEWED_UNTRUSTED", "content": text}
    with directory(repo, ".agents", "research", "reviewed", job) as fd:
        write_new(fd, f"{provider}-{digest}.json", (json.dumps(payload, ensure_ascii=True) + "\n").encode())
    result["status"] = "REVIEWED_UNTRUSTED"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job_id")
    parser.add_argument("provider", choices=sorted(PROVIDERS))
    parser.add_argument("--approve-sha256", help="human-reviewed digest; never supply from an agent")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    try:
        result = intake(repo, args.job_id, args.provider, args.approve_sha256)
    except (ValueError, OSError) as error:
        print(json.dumps({"status": "BLOCKED", "reason": type(error).__name__}))
        return 3
    print(json.dumps(result))
    return {"QUARANTINED": 3, "NEEDS_REVIEW": 2, "REVIEWED_UNTRUSTED": 0}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
