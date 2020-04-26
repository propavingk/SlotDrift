//! Integration tests for the independent Rust engine.

use std::path::PathBuf;

fn sample(name: &str) -> String {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.pop();
    path.push("samples");
    path.push(name);
