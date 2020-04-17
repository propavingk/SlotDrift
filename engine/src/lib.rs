//! Independent Rust implementation of the slotdrift arithmetic.
//!
//! This crate exists to cross-check the Python core. It reads the same JSONL
//! export, applies the same documented rules, and prints the same numbers. It
//! deliberately shares no code with the Python implementation, only the
//! format contract in docs/FORMAT.md.
//!
//! Standard library only. No external crates.

use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Commitment {
    Skipped,
    Processed,
    Confirmed,
    Finalized,
}

impl Commitment {
    pub fn parse(value: &str) -> Option<Commitment> {
        match value {
            "skipped" => Some(Commitment::Skipped),
            "processed" => Some(Commitment::Processed),
            "confirmed" => Some(Commitment::Confirmed),
            "finalized" => Some(Commitment::Finalized),
            _ => None,
        }
    }

    pub fn rank(self) -> i32 {
        match self {
            Commitment::Skipped => -1,
            Commitment::Processed => 0,
            Commitment::Confirmed => 1,
            Commitment::Finalized => 2,
        }
    }
}

#[derive(Debug, Clone)]
pub struct Record {
    pub slot: i64,
    pub parent: Option<i64>,
    pub commitment: Commitment,
    pub leader: Option<String>,
    pub blockhash: Option<String>,
}

impl Record {
    pub fn skipped(&self) -> bool {
        self.commitment == Commitment::Skipped
    }
}

/// Minimal JSON object reader for the fields this format uses. Unknown keys
/// are skipped, and nested containers are skipped in a balanced way. This is
/// not a general JSON parser and does not pretend to be one.
/// One decoded key: its name, its raw text, and whether it was a quoted
/// string. Kept as a small type alias so signatures stay readable.
type Field = (String, (String, bool));
type Fields = Vec<Field>;

fn split_top_level(line: &str) -> Result<Fields, String> {
    let bytes: Vec<char> = line.chars().collect();
    let mut i = 0usize;
    let n = bytes.len();
    let skip_ws = |i: &mut usize| {
        while *i < n && (bytes[*i] == ' ' || bytes[*i] == '\t') {
            *i += 1;
        }
    };
    skip_ws(&mut i);
    if i >= n || bytes[i] != '{' {
        return Err("record must be a JSON object".to_string());
    }
    i += 1;
    let mut pairs = Vec::new();
    loop {
        skip_ws(&mut i);
        if i >= n {
            return Err("unterminated object".to_string());
        }
        if bytes[i] == '}' {
            return Ok(pairs);
        }
        if bytes[i] == ',' {
            i += 1;
            continue;
        }
        if bytes[i] != '"' {
            return Err("expected a quoted key".to_string());
        }
        let (key, next) = read_string(&bytes, i)?;
        i = next;
        skip_ws(&mut i);
        if i >= n || bytes[i] != ':' {
            return Err("expected ':' after key".to_string());
        }
        i += 1;
        skip_ws(&mut i);
        let (raw, is_string, next) = read_value(&bytes, i)?;
        i = next;
        pairs.push((key, (raw, is_string)));
    }
}

fn read_string(bytes: &[char], start: usize) -> Result<(String, usize), String> {
    let mut i = start + 1;
    let mut out = String::new();
    while i < bytes.len() {
        let c = bytes[i];
        if c == '\\' {
            i += 1;
            if i >= bytes.len() {
                return Err("bad escape".to_string());
            }
            out.push(bytes[i]);
            i += 1;
            continue;
        }
        if c == '"' {
            return Ok((out, i + 1));
        }
        out.push(c);
        i += 1;
    }
    Err("unterminated string".to_string())
}

fn read_value(bytes: &[char], start: usize) -> Result<(String, bool, usize), String> {
    let mut i = start;
    if i < bytes.len() && bytes[i] == '"' {
        let (value, next) = read_string(bytes, i)?;
        return Ok((value, true, next));
    }
    let mut depth = 0i32;
    let mut pending = String::new();
    while i < bytes.len() {
        let c = bytes[i];
        match c {
            '{' | '[' => {
                depth += 1;
                if depth > 1 {
                    pending.push(c);
                }
            }
            '}' | ']' => {
                if depth == 0 {
                    break;
                }
                depth -= 1;
                if depth > 0 {
                    pending.push(c);
                } else {
                    i += 1;
                    return Ok((pending, false, i));
                }
            }
            ',' if depth == 0 => break,
            _ => pending.push(c),
        }
        i += 1;
    }
    Ok((pending.trim().to_string(), false, i))
}

pub fn parse_line(line: &str) -> Result<Record, String> {
    let pairs = split_top_level(line)?;
    let map: HashMap<String, (String, bool)> = pairs.into_iter().collect();

    let (slot_raw, slot_is_string) = map.get("slot").ok_or("missing required field 'slot'")?;
    if *slot_is_string {
        return Err("field 'slot' must be an integer".to_string());
    }
    let slot: i64 = slot_raw
        .parse()
        .map_err(|_| "field 'slot' must be an integer")?;
    if slot < 0 {
        return Err("field 'slot' must be >= 0".to_string());
    }

    let (commitment_raw, commitment_is_string) = map
        .get("commitment")
        .ok_or("missing required field 'commitment'")?;
    if !*commitment_is_string {
        return Err(
            "commitment must be one of skipped, processed, confirmed, finalized".to_string(),
        );
    }
    let commitment = Commitment::parse(commitment_raw)
        .ok_or("commitment must be one of skipped, processed, confirmed, finalized")?;

    let mut parent: Option<i64> = None;
    if let Some((raw, is_string)) = map.get("parent") {
        if raw == "null" && !*is_string {
            parent = None;
        } else {
            if *is_string {
                return Err("field 'parent' must be an integer".to_string());
            }
            let parsed: i64 = raw
                .parse()
                .map_err(|_| "field 'parent' must be an integer")?;
            if parsed < 0 {
                return Err("field 'parent' must be >= 0".to_string());
            }
            parent = Some(parsed);
        }
    }

    if let Some((raw, is_string)) = map.get("tx_count") {
        if !(raw == "null" && !*is_string) {
            if *is_string {
                return Err("field 'tx_count' must be an integer".to_string());
            }
            let parsed: i64 = raw
                .parse()
                .map_err(|_| "field 'tx_count' must be an integer")?;
            if parsed < 0 {
                return Err("field 'tx_count' must be >= 0".to_string());
            }
        }
    }

    let mut leader: Option<String> = None;
    if let Some((raw, is_string)) = map.get("leader") {
        if !(raw == "null" && !*is_string) {
            if !*is_string || raw.is_empty() {
                return Err("field 'leader' must be a non-empty string".to_string());
            }
            leader = Some(raw.clone());
        }
    }

    let mut blockhash: Option<String> = None;
    if let Some((raw, is_string)) = map.get("blockhash") {
        if !(raw == "null" && !*is_string) {
            if !*is_string || raw.is_empty() {
                return Err("field 'blockhash' must be a non-empty string".to_string());
            }
            blockhash = Some(raw.clone());
        }
    }

    if commitment != Commitment::Skipped && parent.is_none() {
        return Err("a produced slot must carry a parent".to_string());
    }
    if commitment == Commitment::Skipped && blockhash.is_some() {
        return Err("a skipped slot cannot carry a blockhash".to_string());
    }
    Ok(Record {
        slot,
        parent,
        commitment,
        leader,
        blockhash,
    })
}

pub fn parse_text(text: &str) -> (Vec<Record>, Vec<(usize, String)>) {
    let mut records = Vec::new();
    let mut errors = Vec::new();
    for (index, line) in text.lines().enumerate() {
        if line.trim().is_empty() {
            continue;
        }
        match parse_line(line) {
            Ok(record) => records.push(record),
            Err(message) => errors.push((index + 1, format!("line {}: {}", index + 1, message))),
        }
    }
    (records, errors)
}

#[derive(Debug, Default, Clone)]
pub struct LeaderStats {
    pub scheduled: usize,
    pub skipped: usize,
    pub produced: usize,
}

#[derive(Debug, Default)]
pub struct Continuity {
    pub min_slot: Option<i64>,
    pub max_slot: Option<i64>,
    pub missing: Vec<i64>,
    pub duplicate_slots: BTreeMap<i64, usize>,
    pub skipped: Vec<i64>,
    pub parent_anomalies: Vec<(i64, Option<i64>, String)>,
    pub leaders: BTreeMap<String, LeaderStats>,
}

pub fn analyze_continuity(records: &[Record]) -> Continuity {
    let mut out = Continuity::default();
    if records.is_empty() {
        return out;
    }
    let mut by_slot: BTreeMap<i64, Vec<&Record>> = BTreeMap::new();
    for record in records {
        by_slot.entry(record.slot).or_default().push(record);
    }
    let min_slot = *by_slot.keys().next().unwrap();
    let max_slot = *by_slot.keys().next_back().unwrap();
    out.min_slot = Some(min_slot);
    out.max_slot = Some(max_slot);

    for slot in min_slot..=max_slot {
        if !by_slot.contains_key(&slot) {
            out.missing.push(slot);
        }
    }
    for (slot, group) in &by_slot {
        if group.len() > 1 {
            out.duplicate_slots.insert(*slot, group.len());
        }
    }
    let skipped_slots: BTreeSet<i64> = records
        .iter()
        .filter(|r| r.skipped())
        .map(|r| r.slot)
        .collect();
    out.skipped = skipped_slots.iter().copied().collect();

    let present: BTreeSet<i64> = by_slot.keys().copied().collect();
    for record in records.iter().filter(|r| !r.skipped()) {
        let parent = match record.parent {
            Some(p) => p,
            None => continue,
        };
        if !present.contains(&parent) {
            if parent < min_slot {
                continue;
            }
            out.parent_anomalies.push((
                record.slot,
                Some(parent),
                "parent absent from export".to_string(),
            ));
            continue;
        }
        if parent >= record.slot {
            out.parent_anomalies.push((
                record.slot,
                Some(parent),
                "parent not earlier than block".to_string(),
            ));
            continue;
        }
        if skipped_slots.contains(&parent) {
            out.parent_anomalies.push((
                record.slot,
                Some(parent),
                "parent slot is marked skipped".to_string(),
            ));
            continue;
        }
        if parent < record.slot - 1 {
            let bridge: Vec<i64> = (parent + 1..record.slot).collect();
            let not_skipped = bridge.iter().any(|s| !skipped_slots.contains(s));
            if not_skipped {
                out.parent_anomalies.push((
                    record.slot,
                    Some(parent),
                    "step over slots not marked skipped".to_string(),
                ));
            }
        }
    }
    for record in records {
        if let Some(leader) = &record.leader {
            let stats = out.leaders.entry(leader.clone()).or_default();
            stats.scheduled += 1;
            if record.skipped() {
                stats.skipped += 1;
            } else {
                stats.produced += 1;
            }
        }
    }
    out
}

#[derive(Debug, Clone)]
pub struct OrphanSegment {
    pub start_slot: i64,
    pub end_slot: i64,
    pub length: usize,
    pub root_parent: Option<i64>,
    pub processed: usize,
    pub finalized: usize,
}

#[derive(Debug, Default)]
pub struct Forks {
    pub duplicate_slots: BTreeMap<i64, Vec<String>>,
    pub orphan_segments: Vec<OrphanSegment>,
    pub orphan_count: usize,
    pub canonical_tip: Option<i64>,
}

fn best_record<'a>(group: &[&'a Record]) -> &'a Record {
    // Strongest commitment, then highest slot, then smallest blockhash.
    let mut best = group[0];
    for candidate in group.iter().skip(1) {
        let better = candidate.commitment.rank() > best.commitment.rank()
            || (candidate.commitment.rank() == best.commitment.rank()
                && (candidate.slot > best.slot
                    || (candidate.slot == best.slot
                        && candidate.blockhash.clone().unwrap_or_default()
                            < best.blockhash.clone().unwrap_or_default())));
        if better {
            best = candidate;
        }
    }
    best
}

pub fn find_forks(records: &[Record]) -> Forks {
    let mut out = Forks::default();
    let produced: Vec<&Record> = records.iter().filter(|r| !r.skipped()).collect();
    if produced.is_empty() {
        return out;
    }
    let mut by_slot: BTreeMap<i64, Vec<&Record>> = BTreeMap::new();
    for record in records {
        by_slot.entry(record.slot).or_default().push(record);
    }
    for (slot, group) in &by_slot {
        let mut hashes: BTreeSet<String> = BTreeSet::new();
        for record in group {
            if let Some(hash) = &record.blockhash {
                hashes.insert(hash.clone());
            }
        }
        if hashes.len() > 1 {
            out.duplicate_slots
                .insert(*slot, hashes.into_iter().collect());
        }
    }
    let mut best: BTreeMap<i64, &Record> = BTreeMap::new();
    for (slot, group) in &by_slot {
        let produced_group: Vec<&Record> = group.iter().copied().filter(|r| !r.skipped()).collect();
        let chosen = if produced_group.is_empty() {
            group[0]
        } else {
            best_record(&produced_group)
        };
        best.insert(*slot, chosen);
    }
    let mut tip = produced[0];
    for candidate in produced.iter().skip(1) {
        let better = candidate.commitment.rank() > tip.commitment.rank()
            || (candidate.commitment.rank() == tip.commitment.rank()
                && (candidate.slot > tip.slot
                    || (candidate.slot == tip.slot
                        && candidate.blockhash.clone().unwrap_or_default()
                            < tip.blockhash.clone().unwrap_or_default())));
        if better {
            tip = candidate;
        }
    }
    out.canonical_tip = Some(tip.slot);
