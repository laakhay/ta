use crate::contracts::RustExecutionPayload;
use crate::dataset::DatasetPartitionKey;

use super::backend::{ExecutePlanError, ExecutePlanPayload, KernelStepRequest};
use super::kernel_registry::KernelId;

pub(crate) fn parse_execute_plan_payload(
    payload: &RustExecutionPayload,
) -> Result<ExecutePlanPayload, ExecutePlanError> {
    payload
        .validate()
        .map_err(ExecutePlanError::InvalidPayload)?;

    let mut requests = Vec::with_capacity(payload.requests.len());
    for request in &payload.requests {
        let kernel_id = KernelId::from_name(&request.kernel_id)
            .ok_or_else(|| ExecutePlanError::UnsupportedKernelId(request.kernel_id.clone()))?;
        requests.push(KernelStepRequest {
            node_id: request.node_id,
            kernel_id,
            input_field: request.input_field.clone(),
            kwargs: request.kwargs.clone(),
        });
    }

    Ok(ExecutePlanPayload {
        dataset_id: payload.dataset_id,
        partition_key: DatasetPartitionKey {
            symbol: payload.partition.symbol.clone(),
            timeframe: payload.partition.timeframe.clone(),
            source: payload.partition.source.clone(),
        },
        requests,
    })
}
