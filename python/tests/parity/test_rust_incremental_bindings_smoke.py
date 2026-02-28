from __future__ import annotations

import ta_py


def test_incremental_lifecycle_smoke() -> None:
    backend = ta_py.incremental_initialize()
    requests = [
        {
            "node_id": 1,
            "kernel_id": "rsi",
            "input_field": "close",
            "kwargs": {"period": 2.0},
        }
    ]

    out1 = ta_py.incremental_step(backend, requests, {"close": 10.0}, 1)
    out2 = ta_py.incremental_step(backend, requests, {"close": 11.0}, 2)
    snap = ta_py.incremental_snapshot(backend)
    out3 = ta_py.incremental_step(backend, requests, {"close": 12.0}, 3)

    replay = ta_py.incremental_replay(backend, snap, requests, [{"close": 12.0}])

    assert isinstance(out1, dict)
    assert isinstance(out2, dict)
    assert isinstance(out3, dict)
    assert isinstance(replay, list)
    assert len(replay) == 1
    assert replay[0] == out3
