#ifndef TA_ENGINE_H
#define TA_ENGINE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum ta_status_code {
    TA_STATUS_OK = 0,
    TA_STATUS_INVALID_INPUT = 1,
    TA_STATUS_SHAPE_MISMATCH = 2,
    TA_STATUS_INTERNAL_ERROR = 255,
} ta_status_code;

uint32_t ta_engine_abi_version(void);

#ifdef __cplusplus
}
#endif

#endif
