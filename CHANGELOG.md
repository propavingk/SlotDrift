# Changelog

All notable changes to SlotDrift are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- Rule tables are being reorganised for the next patch.

## [1.0.1] - 2026-06-23

### Fixed

- The parser validates `tx_count` and string field types in both engines, so a
  snapshot that Python accepts is never silently accepted by the Rust engine.
- Parity check added for every fixture, which caught the `tx_count` gap.

## [1.0.0] - 2025-09-16

### Added

- Stable CLI contract: `analyze`, `forks` and `leaders` subcommands with exit
  codes 0, 1 and 2.
- `docs/FORMAT.md` as the written contract for input, output and rules.
- Deterministic JSON report with fixed keys.

## [0.9.0] - 2024-06-11

### Added

- Rust engine (`engine/`) as an independent second implementation.
- `key: value` output from the engine for cross-implementation comparison.
- `scripts/parity.py` comparing both engines on every fixture.

## [0.7.0] - 2021-10-19

### Added

- `--limit` with an explicit `... N more` truncation line.
- Boundary parents below the window are documented as expected, not anomalies.

## [0.6.0] - 2020-11-10

### Added

- JSON report: `analyze --format json` with stable key order.
- Parse errors are collected with line numbers instead of aborting the run.

## [0.5.0] - 2019-09-24

### Added
