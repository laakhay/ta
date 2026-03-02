use crate::core::metadata::indicator_catalog;

use super::contracts::RuntimeCatalogEntry;

pub fn runtime_catalog() -> Vec<RuntimeCatalogEntry> {
    let mut out: Vec<RuntimeCatalogEntry> = indicator_catalog()
        .iter()
        .map(RuntimeCatalogEntry::from_meta)
        .collect();
    out.sort_by(|a, b| a.id.cmp(&b.id));
    out
}
