#!/usr/bin/env python3
"""conftest.py — v7.2 fix: `pytest tests/` ab async test functions bhi chalata hai.

Pehle pytest-asyncio ke bina async tests fail hote the
("async def functions are not natively supported").
Ye hook bina kisi extra dependency ke async tests ko asyncio.run() se
chala deta hai — `python3 tests/test_x.py` direct-run bhi pehle jaisa hi hai.
"""
import asyncio
import inspect


def pytest_pyfunc_call(pyfuncitem):
    testfunction = pyfuncitem.obj
    if inspect.iscoroutinefunction(testfunction):
        funcargs = {
            name: pyfuncitem.funcargs[name]
            for name in pyfuncitem._fixtureinfo.argnames
        }
        asyncio.run(testfunction(**funcargs))
        return True
    return None
