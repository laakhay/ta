use std::collections::HashSet;

use ta_engine::metadata::indicator_catalog;

#[test]
fn ids_are_unique() {
    let catalog = indicator_catalog();
    let mut ids = HashSet::new();
    for indicator in catalog {
        assert!(
            ids.insert(indicator.id),
            "duplicate indicator id found in catalog: {}",
            indicator.id
        );
    }
}

#[test]
fn aliases_are_unique_and_not_conflicting_with_ids() {
    let catalog = indicator_catalog();
    let mut ids = HashSet::new();
    for indicator in catalog {
        ids.insert(indicator.id.to_ascii_lowercase());
    }

    let mut aliases = HashSet::new();
    for indicator in catalog {
        for alias in indicator.aliases {
            let key = alias.to_ascii_lowercase();
            assert!(
                !ids.contains(&key) || key == indicator.id.to_ascii_lowercase(),
                "alias '{}' conflicts with another indicator id",
                alias
            );
            assert!(
                aliases.insert(key),
                "duplicate alias found in catalog: {}",
                alias
            );
        }
    }
}

#[test]
fn catalog_is_deterministically_sorted_by_id() {
    let catalog = indicator_catalog();
    for window in catalog.windows(2) {
        let a = window[0].id;
        let b = window[1].id;
        assert!(a <= b, "catalog must be sorted by id: '{}' then '{}'", a, b);
    }
}

#[test]
fn outputs_have_names_and_descriptions() {
    for indicator in indicator_catalog() {
        assert!(
            !indicator.outputs.is_empty(),
            "indicator '{}' must declare at least one output",
            indicator.id
        );
        for output in indicator.outputs {
            assert!(
                !output.name.trim().is_empty(),
                "indicator '{}' has output with empty name",
                indicator.id
            );
            assert!(
                !output.description.trim().is_empty(),
                "indicator '{}' output '{}' has empty description",
                indicator.id,
                output.name
            );
        }
    }
}

