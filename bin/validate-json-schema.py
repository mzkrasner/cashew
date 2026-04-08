#!/usr/bin/env python3
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("jsonschema module is required for Cashew schema validation", file=sys.stderr)
    sys.exit(2)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: validate-json-schema.py <schema.json> <data.json>", file=sys.stderr)
        return 2

    schema_path = Path(sys.argv[1])
    data_path = Path(sys.argv[2])

    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if not errors:
        return 0

    for err in errors:
        path = ".".join(str(p) for p in err.absolute_path) or "<root>"
        print(f"{path}: {err.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
