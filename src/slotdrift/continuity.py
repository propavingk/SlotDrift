"""Continuity analysis: gaps, skips, parent links and per-leader skip rates.

The mental model is a window of slots, min_slot..max_slot. Every slot in the
window should appear exactly once, either as a produced block or as an explicit
skipped record. Anything else is reported:

- missing: the slot number falls inside the window but no record exists.
- duplicate: more than one record claims the same slot number.
- parent anomaly: a produced block points at a parent that is absent from the
  export, points at itself or a later slot, or skips over slots that are not
  marked skipped.
- unexplained step: parent is below slot-1 and the intermediate slots are not
