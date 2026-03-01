use serde_json::{Map, Number, Value};

use crate::core::metadata::{IndicatorMeta, IndicatorParamKind};

use super::contracts::ComputeRuntimeError;

pub fn normalize_params_for(
    meta: &IndicatorMeta,
    raw: &Value,
) -> Result<Value, ComputeRuntimeError> {
    let raw_map = match raw {
        Value::Null => Map::new(),
        Value::Object(map) => map.clone(),
        _ => {
            return Err(ComputeRuntimeError::new(
                "invalid_param",
                "params must be a JSON object",
            ));
        }
    };

    let mut canonical_in = Map::new();
    for (key, value) in raw_map {
        let target = resolve_param_target(meta, &key).ok_or_else(|| {
            ComputeRuntimeError::new(
                "invalid_param",
                format!("unknown parameter '{key}' for indicator '{}'", meta.id),
            )
        })?;
        if canonical_in.contains_key(target) {
            return Err(ComputeRuntimeError::new(
                "invalid_param",
                format!("duplicate parameter assignment for '{target}'"),
            ));
        }
        canonical_in.insert(target.to_string(), value);
    }

    let mut normalized = Map::new();
    for param in meta.params {
        let value = match canonical_in.remove(param.name) {
            Some(value) => coerce_param_value(meta, param.name, param.kind, value)?,
            None => {
                if let Some(default) = param.default {
                    coerce_default(meta, param.name, param.kind, default)?
                } else if param.required {
                    return Err(ComputeRuntimeError::new(
                        "invalid_param",
                        format!("missing required parameter '{}'", param.name),
                    ));
                } else {
                    continue;
                }
            }
        };

        if let Some(min) = param.min {
            ensure_min(param.name, &value, min)?;
        }
        if let Some(max) = param.max {
            ensure_max(param.name, &value, max)?;
        }

        normalized.insert(param.name.to_string(), value);
    }

    Ok(Value::Object(normalized))
}

fn resolve_param_target<'a>(meta: &'a IndicatorMeta, key: &str) -> Option<&'a str> {
    if let Some(param) = meta
        .params
        .iter()
        .find(|param| param.name.eq_ignore_ascii_case(key))
    {
        return Some(param.name);
    }
    meta.param_aliases
        .iter()
        .find(|alias| alias.alias.eq_ignore_ascii_case(key))
        .map(|alias| alias.target)
}

fn coerce_default(
    meta: &IndicatorMeta,
    name: &str,
    kind: IndicatorParamKind,
    default: &str,
) -> Result<Value, ComputeRuntimeError> {
    let parsed =
        match kind {
            IndicatorParamKind::Integer => default
                .parse::<i64>()
                .map(Value::from)
                .map_err(|_| invalid_param(meta, name, "default integer parse failed"))?,
            IndicatorParamKind::Float => {
                let value = default
                    .parse::<f64>()
                    .map_err(|_| invalid_param(meta, name, "default float parse failed"))?;
                Value::Number(Number::from_f64(value).ok_or_else(|| {
                    invalid_param(meta, name, "default float cannot be represented")
                })?)
            }
            IndicatorParamKind::Boolean => match default {
                "true" | "1" => Value::Bool(true),
                "false" | "0" => Value::Bool(false),
                _ => return Err(invalid_param(meta, name, "default bool parse failed")),
            },
            IndicatorParamKind::String => Value::String(default.to_string()),
        };
    Ok(parsed)
}

fn coerce_param_value(
    meta: &IndicatorMeta,
    name: &str,
    kind: IndicatorParamKind,
    value: Value,
) -> Result<Value, ComputeRuntimeError> {
    match kind {
        IndicatorParamKind::Integer => match value {
            Value::Number(n) if n.is_i64() || n.is_u64() => Ok(Value::Number(n)),
            Value::String(s) => s
                .parse::<i64>()
                .map(Value::from)
                .map_err(|_| invalid_param(meta, name, "must be an integer")),
            _ => Err(invalid_param(meta, name, "must be an integer")),
        },
        IndicatorParamKind::Float => match value {
            Value::Number(n) => {
                let as_f64 = n
                    .as_f64()
                    .ok_or_else(|| invalid_param(meta, name, "must be numeric"))?;
                let repr = Number::from_f64(as_f64)
                    .ok_or_else(|| invalid_param(meta, name, "must be finite"))?;
                Ok(Value::Number(repr))
            }
            Value::String(s) => {
                let parsed = s
                    .parse::<f64>()
                    .map_err(|_| invalid_param(meta, name, "must be numeric"))?;
                Ok(Value::Number(Number::from_f64(parsed).ok_or_else(
                    || invalid_param(meta, name, "must be finite"),
                )?))
            }
            _ => Err(invalid_param(meta, name, "must be numeric")),
        },
        IndicatorParamKind::Boolean => match value {
            Value::Bool(flag) => Ok(Value::Bool(flag)),
            Value::String(s) if s.eq_ignore_ascii_case("true") || s == "1" => Ok(Value::Bool(true)),
            Value::String(s) if s.eq_ignore_ascii_case("false") || s == "0" => {
                Ok(Value::Bool(false))
            }
            _ => Err(invalid_param(meta, name, "must be a boolean")),
        },
        IndicatorParamKind::String => match value {
            Value::String(s) => Ok(Value::String(s)),
            _ => Err(invalid_param(meta, name, "must be a string")),
        },
    }
}

fn ensure_min(name: &str, value: &Value, min: f64) -> Result<(), ComputeRuntimeError> {
    let numeric = value.as_f64().ok_or_else(|| {
        ComputeRuntimeError::new("invalid_param", format!("'{name}' must be numeric"))
    })?;
    if numeric < min {
        return Err(ComputeRuntimeError::new(
            "invalid_param",
            format!("'{name}' must be >= {min}"),
        ));
    }
    Ok(())
}

fn ensure_max(name: &str, value: &Value, max: f64) -> Result<(), ComputeRuntimeError> {
    let numeric = value.as_f64().ok_or_else(|| {
        ComputeRuntimeError::new("invalid_param", format!("'{name}' must be numeric"))
    })?;
    if numeric > max {
        return Err(ComputeRuntimeError::new(
            "invalid_param",
            format!("'{name}' must be <= {max}"),
        ));
    }
    Ok(())
}

fn invalid_param(meta: &IndicatorMeta, name: &str, reason: &str) -> ComputeRuntimeError {
    ComputeRuntimeError::new(
        "invalid_param",
        format!("indicator '{}' param '{name}': {reason}", meta.id),
    )
}
