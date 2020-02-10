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
