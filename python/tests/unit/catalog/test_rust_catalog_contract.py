from __future__ import annotations


def test_rust_catalog_contract_shape():
    import ta_py

    if not hasattr(ta_py, "indicator_catalog_contract"):
        return

    contract = ta_py.indicator_catalog_contract()
    assert isinstance(contract, dict)
    assert contract.get("contract_version") == 1
    indicators = contract.get("indicators")
    assert isinstance(indicators, list)
    assert len(indicators) > 0
    first = indicators[0]
    assert isinstance(first.get("visual"), dict)
