#!/usr/bin/env python3
"""Export changed entries from the tested NFSIISE text format as JSON."""

import argparse
import json
import struct
from pathlib import Path


def entries(data: bytes) -> list[bytes]:
    if len(data) < 12:
        raise ValueError("file is too short")
    start = struct.unpack_from("<I", data, 8)[0]
    if start < 12 or start % 12 or start > len(data):
        raise ValueError("invalid table size")
    result = []
    for position in range(0, start, 12):
        offset = struct.unpack_from("<I", data, position + 8)[0]
        if not start <= offset < len(data):
            raise ValueError(f"invalid string offset in entry {position // 12}")
        end = data.find(b"\0", offset)
        if end < 0:
            raise ValueError(f"unterminated string in entry {position // 12}")
        result.append(data[offset:end])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("translated", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    original = entries(args.original.read_bytes())
    translated = entries(args.translated.read_bytes())
    if len(original) != len(translated):
        raise ValueError("files have different entry counts")
    changes = {}
    for index, (before, after) in enumerate(zip(original, translated)):
        if before != after:
            changes[str(index)] = after.replace(b"\x98", b"\xff").decode("cp1251")
    result = {
        "format": "nfs2se-translation-v1",
        "language": "ru",
        "encoding": "cp1251-with-ya-at-98",
        "entry_count": len(original),
        "entries": changes,
    }
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(f"Exported {len(changes)} changed entries to {args.output}")


if __name__ == "__main__":
    main()
