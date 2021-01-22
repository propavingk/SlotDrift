## What this changes

## Why

## Checklist

- [ ] `PYTHONPATH=src python -m unittest discover -s tests -v` passes
- [ ] `cargo test --manifest-path engine/Cargo.toml` passes
- [ ] `python scripts/parity.py` reports every fixture agreeing (required if any rule changed)
