## What this changes

## Why

## Checklist

- [ ] `PYTHONPATH=src python -m unittest discover -s tests -v` passes
- [ ] `cargo test --manifest-path engine/Cargo.toml` passes
- [ ] `python scripts/parity.py` reports every fixture agreeing (required if any rule changed)
- [ ] `python scripts/verify.py` exits 0
- [ ] Report shape changes: real `analyze` output pasted above
- [ ] `docs/FORMAT.md` updated if a field, rule or exit code changed
