import pytest
from utils.rate_limit_send import rate_limited_gather


async def _ok():
    pass


async def _fail():
    raise RuntimeError("send failed")


async def test_empty_list():
    succ, unsucc = await rate_limited_gather([])
    assert succ == 0
    assert unsucc == 0


async def test_all_success():
    coros = [_ok() for _ in range(5)]
    succ, unsucc = await rate_limited_gather(coros)
    assert succ == 5
    assert unsucc == 0


async def test_all_fail():
    coros = [_fail() for _ in range(4)]
    succ, unsucc = await rate_limited_gather(coros)
    assert succ == 0
    assert unsucc == 4


async def test_mixed_success_fail():
    coros = [_ok() for _ in range(3)] + [_fail() for _ in range(2)]
    succ, unsucc = await rate_limited_gather(coros)
    assert succ == 3
    assert unsucc == 2


async def test_single_success():
    succ, unsucc = await rate_limited_gather([_ok()])
    assert succ == 1
    assert unsucc == 0


async def test_single_fail():
    succ, unsucc = await rate_limited_gather([_fail()])
    assert succ == 0
    assert unsucc == 1


async def test_succ_plus_unsucc_equals_total():
    n = 10
    coros = [_ok() if i % 3 != 0 else _fail() for i in range(n)]
    succ, unsucc = await rate_limited_gather(coros)
    assert succ + unsucc == n
