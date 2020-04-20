//! Command line front end for the Rust engine.
//!
//! Prints key: value lines, one per line, so the parity script can compare
//! the numbers against the Python implementation without sharing any code.
//!
//! Exit codes: 0 clean, 1 findings, 2 usage or input error.

use std::env;
use std::fs;
use std::process;

use slotdrift_engine::{analyze_continuity, find_forks, parse_text};

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() == 2 && args[1] == "--version" {
        println!("slotdrift-engine 0.1.0");
        return;
    }
    if args.len() != 3 || args[1] != "analyze" {
        eprintln!("usage: slotdrift-engine analyze <export.jsonl>");
        process::exit(2);
    }
    let path = &args[2];
    let text = match fs::read_to_string(path) {
        Ok(text) => text,
        Err(error) => {
            eprintln!("slotdrift-engine: cannot read {}: {}", path, error);
            process::exit(2);
        }
    };
    let (records, errors) = parse_text(&text);
    let continuity = analyze_continuity(&records);
    let forks = find_forks(&records);
    let missing = continuity.missing.len();
    let duplicates = continuity.duplicate_slots.len();
    let anomalies = continuity.parent_anomalies.len();
    let duplicate_extra: usize = continuity
        .duplicate_slots
        .values()
        .map(|count| count.saturating_sub(1))
        .sum();
    let findings = missing
        + duplicate_extra
        + anomalies
        + forks.duplicate_slots.len()
        + forks.orphan_count
        + errors.len();

    let window = match (continuity.min_slot, continuity.max_slot) {
        (Some(min), Some(max)) => format!("{}..{}", min, max),
        _ => "empty".to_string(),
