.PHONY: help test verify run clean

PYTHON ?= python
export PYTHONPATH := src

help:
	@echo "slotdrift targets:"
	@echo "  make test    run the Python unit tests and the Rust engine tests"
	@echo "  make verify  run the repository quality gate (scripts/verify.py)"
	@echo "  make run     analyze the cluster sample and print the report"
	@echo "  make parity  compare the Python and Rust numbers on the samples"
	@echo "  make clean   remove caches and build output"

test:
	$(PYTHON) -m unittest discover -s tests -v
	cargo test --manifest-path engine/Cargo.toml

verify:
	$(PYTHON) scripts/verify.py

run:
	$(PYTHON) -m slotdrift analyze samples/cluster-window.jsonl

parity:
	$(PYTHON) scripts/parity.py

clean:
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"
	-rm -rf engine/target .pytest_cache
