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
