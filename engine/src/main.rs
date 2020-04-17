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
