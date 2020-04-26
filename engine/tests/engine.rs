//! Integration tests for the independent Rust engine.

use std::path::PathBuf;

fn sample(name: &str) -> String {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.pop();
    path.push("samples");
    path.push(name);
    std::fs::read_to_string(path).expect("fixture readable")
}

#[test]
fn clean_window_has_no_findings() {
    let (records, errors) = slotdrift_engine::parse_text(&sample("clean-window.jsonl"));
    assert_eq!(records.len(), 30);
    assert!(errors.is_empty());
    let continuity = slotdrift_engine::analyze_continuity(&records);
