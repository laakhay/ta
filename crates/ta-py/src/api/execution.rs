use std::collections::BTreeMap;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use ta_engine::contracts::{RustExecutionGraph, RustExecutionPartition, RustExecutionPayload};
use ta_engine::dataset::DatasetPartitionKey;
use ta_engine::incremental::backend::{self, ExecutePlanPayload, IncrementalBackend};

use crate::conversions::{
    extract_node_id, extract_scalar_string, incremental_map_to_pydict,
    incremental_series_map_to_pydict, parse_contract_requests, parse_events, parse_requests,
    parse_tick,
};
use crate::errors::map_execute_plan_error;
use crate::state::{
    next_backend_id, next_snapshot_id, with_backends_mut, with_snapshots, with_snapshots_mut,
};

#[pyfunction]
pub(crate) fn incremental_initialize() -> PyResult<u64> {
    let mut backend = IncrementalBackend::default();
    backend.initialize();
    let id = next_backend_id();
    with_backends_mut(|map| {
        map.insert(id, backend);
        id
    })
}

#[pyfunction]
pub(crate) fn incremental_step(
    py: Python<'_>,
    backend_id: u64,
    requests: &Bound<'_, PyList>,
    tick: &Bound<'_, PyDict>,
    event_index: u64,
) -> PyResult<PyObject> {
    let parsed_requests = parse_requests(requests)?;
    let parsed_tick = parse_tick(tick)?;

    let out = with_backends_mut(|map| {
        let backend = map.get_mut(&backend_id).ok_or_else(|| {
            pyo3::exceptions::PyKeyError::new_err(format!("backend id {backend_id} not found"))
        })?;
        Ok::<_, PyErr>(backend.step(event_index, &parsed_requests, &parsed_tick))
    })??;

    incremental_map_to_pydict(py, &out)
}

#[pyfunction]
pub(crate) fn incremental_snapshot(backend_id: u64) -> PyResult<u64> {
    let snapshot = with_backends_mut(|map| {
        let backend = map.get_mut(&backend_id).ok_or_else(|| {
            pyo3::exceptions::PyKeyError::new_err(format!("backend id {backend_id} not found"))
        })?;
        Ok::<_, PyErr>(backend.snapshot())
    })??;

    let snapshot_id = next_snapshot_id();
    with_snapshots_mut(|snaps| {
        snaps.insert(snapshot_id, snapshot);
        snapshot_id
    })
}

#[pyfunction]
pub(crate) fn incremental_replay(
    py: Python<'_>,
    backend_id: u64,
    snapshot_id: u64,
    requests: &Bound<'_, PyList>,
    events: &Bound<'_, PyList>,
) -> PyResult<PyObject> {
    let snapshot = with_snapshots(|snaps| {
        snaps.get(&snapshot_id).cloned().ok_or_else(|| {
            pyo3::exceptions::PyKeyError::new_err(format!("snapshot id {snapshot_id} not found"))
        })
    })??;

    let parsed_requests = parse_requests(requests)?;
    let parsed_events = parse_events(events)?;

    let replay_out = with_backends_mut(|map| {
        let backend = map.get_mut(&backend_id).ok_or_else(|| {
            pyo3::exceptions::PyKeyError::new_err(format!("backend id {backend_id} not found"))
        })?;

        backend
            .restore(snapshot)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        Ok::<_, PyErr>(backend.replay(&parsed_requests, &parsed_events))
    })??;

    let py_list = PyList::empty(py);
    for step in replay_out {
        py_list.append(incremental_map_to_pydict(py, &step)?)?;
    }
    Ok(py_list.into_any().unbind())
}

#[pyfunction]
pub(crate) fn execute_plan(
    py: Python<'_>,
    dataset_id: u64,
    symbol: String,
    timeframe: String,
    source: String,
    requests: &Bound<'_, PyList>,
) -> PyResult<PyObject> {
    let parsed_requests = parse_requests(requests)?;
    let payload = ExecutePlanPayload {
        dataset_id,
        partition_key: DatasetPartitionKey {
            symbol,
            timeframe,
            source,
        },
        requests: parsed_requests,
    };
    let out = backend::execute_plan_payload(&payload).map_err(map_execute_plan_error)?;
    incremental_series_map_to_pydict(py, &out)
}

#[pyfunction]
pub(crate) fn execute_plan_payload(
    py: Python<'_>,
    payload: &Bound<'_, PyDict>,
) -> PyResult<PyObject> {
    let dataset_id: u64 = payload
        .get_item("dataset_id")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing dataset_id"))?
        .extract()?;
    let partition = payload
        .get_item("partition")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing partition"))?
        .downcast_into::<PyDict>()?;
    let symbol: String = partition
        .get_item("symbol")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing partition.symbol"))?
        .extract()?;
    let timeframe: String = partition
        .get_item("timeframe")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing partition.timeframe"))?
        .extract()?;
    let source: String = partition
        .get_item("source")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing partition.source"))?
        .extract()?;
    let requests = payload
        .get_item("requests")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing requests"))?
        .downcast_into::<PyList>()?;

    let graph = payload
        .get_item("graph")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing graph"))?
        .downcast_into::<PyDict>()?;
    let root_id: u32 = graph
        .get_item("root_id")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing graph.root_id"))?
        .extract()?;
    let node_order: Vec<u32> = graph
        .get_item("node_order")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing graph.node_order"))?
        .extract()?;
    let nodes_dict = graph
        .get_item("nodes")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing graph.nodes"))?
        .downcast_into::<PyDict>()?;
    let edges_dict = graph
        .get_item("edges")?
        .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing graph.edges"))?
        .downcast_into::<PyDict>()?;

    let mut nodes: BTreeMap<u32, BTreeMap<String, String>> = BTreeMap::new();
    for (k, v) in nodes_dict.iter() {
        let node_id = extract_node_id(&k)?;
        let details = v.downcast::<PyDict>()?;
        let mut map = BTreeMap::new();
        for (dk, dv) in details.iter() {
            map.insert(dk.extract::<String>()?, extract_scalar_string(&dv)?);
        }
        nodes.insert(node_id, map);
    }

    let mut edges = BTreeMap::new();
    for (k, v) in edges_dict.iter() {
        let node_id = extract_node_id(&k)?;
        let child_ids: Vec<u32> = v.extract()?;
        edges.insert(node_id, child_ids);
    }

    let contract_payload = RustExecutionPayload {
        dataset_id,
        partition: RustExecutionPartition {
            symbol,
            timeframe,
            source,
        },
        graph: RustExecutionGraph {
            root_id,
            node_order,
            nodes,
            edges,
        },
        requests: parse_contract_requests(&requests)?,
    };
    let out =
        backend::execute_plan_graph_payload(&contract_payload).map_err(map_execute_plan_error)?;
    incremental_series_map_to_pydict(py, &out)
}
