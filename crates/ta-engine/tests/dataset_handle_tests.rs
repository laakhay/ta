use ta_engine::dataset::{
    create_dataset, dataset_exists, drop_dataset, get_dataset, DatasetRegistryError,
};

#[test]
fn dataset_handle_lifecycle_roundtrip() {
    let id = create_dataset();

    assert!(dataset_exists(id));
    let snapshot = get_dataset(id).expect("dataset should exist");
    assert_eq!(snapshot.id, id);
    assert_eq!(snapshot.partitions.len(), 0);

    drop_dataset(id).expect("drop should succeed");
    assert!(!dataset_exists(id));
}

#[test]
fn unknown_dataset_id_errors() {
    let missing = create_dataset();
    drop_dataset(missing).expect("drop should succeed");
    assert_eq!(
        get_dataset(missing),
        Err(DatasetRegistryError::UnknownDatasetId(missing))
    );
    assert_eq!(
        drop_dataset(missing),
        Err(DatasetRegistryError::UnknownDatasetId(missing))
    );
}

#[test]
fn dataset_ids_are_monotonic() {
    let first = create_dataset();
    let second = create_dataset();

    assert!(second > first);
    drop_dataset(first).expect("drop first should succeed");
    drop_dataset(second).expect("drop second should succeed");
}
