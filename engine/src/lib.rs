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
