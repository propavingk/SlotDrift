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
    assert_eq!(continuity.missing.len(), 0);
    assert_eq!(continuity.parent_anomalies.len(), 0);
    assert_eq!(continuity.skipped, vec![100_000_010, 100_000_011]);
    let forks = slotdrift_engine::find_forks(&records);
    assert_eq!(forks.orphan_count, 0);
    assert!(forks.orphan_segments.is_empty());
}

#[test]
fn cluster_window_reports_the_designed_findings() {
    let (records, errors) = slotdrift_engine::parse_text(&sample("cluster-window.jsonl"));
    assert_eq!(records.len(), 64);
    assert!(errors.is_empty());
    let continuity = slotdrift_engine::analyze_continuity(&records);
    assert_eq!(continuity.duplicate_slots.len(), 3);
    assert_eq!(continuity.parent_anomalies.len(), 1);
    assert_eq!(continuity.skipped.len(), 3);
    let forks = slotdrift_engine::find_forks(&records);
    assert_eq!(forks.duplicate_slots.len(), 3);
