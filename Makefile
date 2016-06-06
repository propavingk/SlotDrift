.PHONY: help test verify run clean

PYTHON ?= python
export PYTHONPATH := src

help:
	@echo "slotdrift targets:"
	@echo "  make test    run the Python unit tests and the Rust engine tests"
