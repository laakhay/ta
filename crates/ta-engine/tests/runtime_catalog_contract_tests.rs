use ta_engine::metadata::{find_indicator_meta, PlotCapability};
use ta_engine::runtime_catalog;

#[test]
fn runtime_catalog_is_sorted_and_resolves_all_ids() {
    let catalog = runtime_catalog();
    for window in catalog.windows(2) {
        assert!(window[0].id <= window[1].id);
    }
    for entry in catalog {
        assert!(find_indicator_meta(&entry.id).is_some());
    }
}

#[test]
fn event_indicators_are_classified_as_event_only() {
    let catalog = runtime_catalog();
    for entry in catalog.iter().filter(|it| it.category == "event") {
        assert_eq!(entry.plot_capability, PlotCapability::EventOnly);
    }
}
