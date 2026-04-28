from sigilgateapp.domain.result import Err, Ok


def test_ok_and_then_calls_f():
    result = Ok(1).and_then(lambda x: Ok(x + 1))
    assert result == Ok(2)


def test_ok_and_then_propagates_err():
    result = Ok(1).and_then(lambda x: Err("fail"))
    assert result == Err("fail")


def test_err_and_then_skips_f():
    called = []
    result = Err("fail").and_then(lambda x: called.append(x) or Ok(x))
    assert result == Err("fail")
    assert called == []


def test_ok_map_transforms_value():
    result = Ok(2).map(lambda x: x * 3)
    assert result == Ok(6)


def test_err_map_skips_f():
    result = Err("fail").map(lambda x: x * 3)
    assert result == Err("fail")


def test_chain_ok_ok_ok():
    result = (
        Ok(1)
        .and_then(lambda x: Ok(x + 1))
        .and_then(lambda x: Ok(x * 10))
        .map(lambda x: str(x))
    )
    assert result == Ok("20")


def test_chain_short_circuits_on_err():
    steps = []
    result = (
        Ok(1)
        .and_then(lambda x: steps.append("a") or Err("stop"))
        .and_then(lambda x: steps.append("b") or Ok(x))
    )
    assert result == Err("stop")
    assert steps == ["a"]
