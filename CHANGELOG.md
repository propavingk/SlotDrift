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

