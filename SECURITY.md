# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## What slotdrift is, in security terms

slotdrift is an offline analysis tool. It reads a JSONL export of slot records,
validates the fields, and prints a report. It does not:

- open sockets, make HTTP requests, or resolve DNS names;
- execute anything from the input, including field values that resemble code
  or paths;
- write files by default; `--output` writes exactly one report file to the
  path you name;
- run with elevated privileges, install anything, or modify its environment.

The realistic threat model for a tool like this is malformed input:

1. **Parser crashes.** A crafted line might trigger an unhandled exception.
   The parser is covered by tests for every documented validation rule, and
   any crash is treated as a bug.
2. **Resource consumption.** A very large export consumes memory for the
   record list and the per-slot maps. There is no streaming mode yet; a
   multi-gigabyte export is not a supported input today.
3. **Terminal output.** Slot numbers, leader names and blockhashes are
   printed as they appear in the input. If your export contains control
   characters in string fields, your terminal will render them. The tool does
   not sanitize output beyond what the JSON parser already strips.
4. **Path handling in `--output`.** The path is used exactly as given. Running
   the tool as a privileged user against an attacker-controlled output path is
   the same risk class as any CLI that writes a file.

## What slotdrift does not protect against

- It does not verify that the export is truthful. It checks internal
  consistency, not provenance.
- It does not validate blockhashes as real cluster hashes; any non-empty
  string is accepted.
- It is not a monitoring system. A clean report on a stale export says nothing
  about the current chain state.
