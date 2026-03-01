use serde_json::Value;

use super::contracts::ComputeRuntimeError;

pub fn normalize_params(raw: &Value) -> Result<Value, ComputeRuntimeError> {
    if raw.is_null() {
        return Ok(Value::Object(Default::default()));
    }
    if !raw.is_object() {
        return Err(ComputeRuntimeError::new(
            "invalid_param",
            "params must be a JSON object",
        ));
    }
    Ok(raw.clone())
}
