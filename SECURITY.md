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
