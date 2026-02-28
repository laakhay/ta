use std::collections::BTreeMap;

use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyList};
use ta_engine::contracts::RustExecutionRequest;
use ta_engine::incremental::backend::KernelStepRequest;
use ta_engine::incremental::contracts::IncrementalValue;
use ta_engine::incremental::kernel_registry::KernelId;

pub(crate) type IchimokuTuple = (Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>);

pub(crate) fn parse_requests(requests: &Bound<'_, PyList>) -> PyResult<Vec<KernelStepRequest>> {
    let mut out = Vec::with_capacity(requests.len());
    for item in requests.iter() {
        let d = item.downcast::<PyDict>()?;
        let node_id: u32 = d
            .get_item("node_id")?
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing node_id"))?
            .extract()?;
        let kernel_name: String = d
            .get_item("kernel_id")?
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing kernel_id"))?
            .extract()?;
        let input_field: String = d
            .get_item("input_field")?
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing input_field"))?
            .extract()?;
        let kwargs_dict = d
            .get_item("kwargs")?
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing kwargs"))?
            .downcast_into::<PyDict>()?;

        let kernel_id = KernelId::from_name(&kernel_name).ok_or_else(|| {
            pyo3::exceptions::PyValueError::new_err(format!("unsupported kernel_id: {kernel_name}"))
        })?;

        out.push(KernelStepRequest {
            node_id,
            kernel_id,
            input_field,
            kwargs: parse_tick(&kwargs_dict)?,
        });
    }
    Ok(out)
}

pub(crate) fn parse_contract_requests(
    requests: &Bound<'_, PyList>,
) -> PyResult<Vec<RustExecutionRequest>> {
    let mut out = Vec::with_capacity(requests.len());
    for item in requests.iter() {
        let d = item.downcast::<PyDict>()?;
        let node_id: u32 = d
            .get_item("node_id")?
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing node_id"))?
            .extract()?;
        let kernel_id: String = d
            .get_item("kernel_id")?
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing kernel_id"))?
            .extract()?;
        let input_field: String = d
            .get_item("input_field")?
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing input_field"))?
            .extract()?;
        let kwargs_dict = d
            .get_item("kwargs")?
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("missing kwargs"))?
            .downcast_into::<PyDict>()?;
        out.push(RustExecutionRequest {
            node_id,
            kernel_id,
            input_field,
            kwargs: parse_tick(&kwargs_dict)?,
        });
    }
    Ok(out)
}

pub(crate) fn parse_events(
    events: &Bound<'_, PyList>,
) -> PyResult<Vec<BTreeMap<String, IncrementalValue>>> {
    let mut out = Vec::with_capacity(events.len());
    for item in events.iter() {
        let d = item.downcast::<PyDict>()?;
        out.push(parse_tick(d)?);
    }
    Ok(out)
}

pub(crate) fn parse_tick(tick: &Bound<'_, PyDict>) -> PyResult<BTreeMap<String, IncrementalValue>> {
    let mut out = BTreeMap::new();
    for (k, v) in tick.iter() {
        let key: String = k.extract()?;
        let value = if let Ok(n) = v.extract::<f64>() {
            IncrementalValue::Number(n)
        } else if let Ok(b) = v.extract::<bool>() {
            IncrementalValue::Bool(b)
        } else if let Ok(s) = v.extract::<String>() {
            IncrementalValue::Text(s)
        } else {
            IncrementalValue::Null
        };
        out.insert(key, value);
    }
    Ok(out)
}

pub(crate) fn extract_node_id(value: &Bound<'_, PyAny>) -> PyResult<u32> {
    if let Ok(id) = value.extract::<u32>() {
        return Ok(id);
    }
    if let Ok(text) = value.extract::<String>() {
        return text.parse::<u32>().map_err(|_| {
            pyo3::exceptions::PyValueError::new_err(format!("invalid node id: {text}"))
        });
    }
    Err(pyo3::exceptions::PyValueError::new_err(
        "invalid node id type",
    ))
}

pub(crate) fn extract_scalar_string(value: &Bound<'_, PyAny>) -> PyResult<String> {
    if let Ok(text) = value.extract::<String>() {
        return Ok(text);
    }
    if let Ok(v) = value.extract::<bool>() {
        return Ok(v.to_string());
    }
    if let Ok(v) = value.extract::<i64>() {
        return Ok(v.to_string());
    }
    if let Ok(v) = value.extract::<f64>() {
        return Ok(v.to_string());
    }
    Ok(format!("{value:?}"))
}

pub(crate) fn incremental_map_to_pydict(
    py: Python<'_>,
    values: &BTreeMap<u32, IncrementalValue>,
) -> PyResult<PyObject> {
    let d = PyDict::new(py);
    for (k, v) in values {
        match v {
            IncrementalValue::Number(n) => d.set_item(k, n)?,
            IncrementalValue::Bool(b) => d.set_item(k, b)?,
            IncrementalValue::Text(s) => d.set_item(k, s)?,
            IncrementalValue::Null => d.set_item(k, py.None())?,
        }
    }
    Ok(d.into_any().unbind())
}

pub(crate) fn incremental_series_map_to_pydict(
    py: Python<'_>,
    values: &BTreeMap<u32, Vec<IncrementalValue>>,
) -> PyResult<PyObject> {
    let d = PyDict::new(py);
    for (k, series) in values {
        let py_list = PyList::empty(py);
        for v in series {
            match v {
                IncrementalValue::Number(n) => py_list.append(*n)?,
                IncrementalValue::Bool(b) => py_list.append(*b)?,
                IncrementalValue::Text(s) => py_list.append(s)?,
                IncrementalValue::Null => py_list.append(py.None())?,
            }
        }
        d.set_item(k, py_list)?;
    }
    Ok(d.into_any().unbind())
}

pub(crate) fn indicator_meta_to_pydict(
    py: Python<'_>,
    meta: &ta_engine::metadata::IndicatorMeta,
) -> PyResult<PyObject> {
    let d = PyDict::new(py);
    d.set_item("id", meta.id)?;
    d.set_item("display_name", meta.display_name)?;
    d.set_item("category", meta.category)?;
    d.set_item("runtime_binding", meta.runtime_binding)?;

    let aliases = PyList::empty(py);
    for alias in meta.aliases {
        aliases.append(alias)?;
    }
    d.set_item("aliases", aliases)?;

    let param_aliases = PyDict::new(py);
    for alias in meta.param_aliases {
        param_aliases.set_item(alias.alias, alias.target)?;
    }
    d.set_item("param_aliases", param_aliases)?;

    let params = PyList::empty(py);
    for param in meta.params {
        let p = PyDict::new(py);
        p.set_item("name", param.name)?;
        let kind = match param.kind {
            ta_engine::metadata::IndicatorParamKind::Integer => "int",
            ta_engine::metadata::IndicatorParamKind::Float => "float",
            ta_engine::metadata::IndicatorParamKind::Boolean => "bool",
            ta_engine::metadata::IndicatorParamKind::String => "string",
        };
        p.set_item("kind", kind)?;
        p.set_item("required", param.required)?;
        p.set_item("default", param.default)?;
        p.set_item("description", param.description)?;
        p.set_item("min", param.min)?;
        p.set_item("max", param.max)?;
        params.append(p)?;
    }
    d.set_item("params", params)?;

    let outputs = PyList::empty(py);
    for output in meta.outputs {
        let o = PyDict::new(py);
        o.set_item("name", output.name)?;
        o.set_item("kind", output.kind)?;
        o.set_item("description", output.description)?;
        outputs.append(o)?;
    }
    d.set_item("outputs", outputs)?;

    let semantics = PyDict::new(py);
    let required_fields = PyList::empty(py);
    for field in meta.semantics.required_fields {
        required_fields.append(field)?;
    }
    semantics.set_item("required_fields", required_fields)?;

    let optional_fields = PyList::empty(py);
    for field in meta.semantics.optional_fields {
        optional_fields.append(field)?;
    }
    semantics.set_item("optional_fields", optional_fields)?;

    let lookback_params = PyList::empty(py);
    for param in meta.semantics.lookback_params {
        lookback_params.append(param)?;
    }
    semantics.set_item("lookback_params", lookback_params)?;
    semantics.set_item("default_lookback", meta.semantics.default_lookback)?;
    semantics.set_item("warmup_policy", meta.semantics.warmup_policy)?;
    d.set_item("semantics", semantics)?;

    Ok(d.into_any().unbind())
}
