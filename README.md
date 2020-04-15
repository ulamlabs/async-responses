# async-responses

[![Documentation Status](https://readthedocs.org/projects/async-responses/badge/?version=latest)](http://async-responses.readthedocs.io/en/latest/?badge=latest) [![codecov](https://codecov.io/gh/ulamlabs/async-responses/branch/master/graph/badge.svg)](https://codecov.io/gh/ulamlabs/async-responses) ![Python package](https://github.com/ulamlabs/async-responses/workflows/Python%20package/badge.svg) ![Upload Python Package](https://github.com/ulamlabs/async-responses/workflows/Upload%20Python%20Package/badge.svg)

async-responses is a library providing an easy way to mock aiohttp responses inspired by [aioresponses](https://github.com/pnuckowski/aioresponses).

## Installation

Library is available on PyPi, you can simply install it using `pip`.
```
$ pip install async-responses
```

## Usage

```
import pytest
from async_responses import AsyncResponses


@pytest.fixture
def ar(request, mocker, loop):
    params = request.node.get_closest_marker('ar')
    kwargs = params.kwargs if params else {}

    with AsyncResponses(mocker.mock_module, loop, **kwargs) as m:
        yield m
```

### With dict as handler

Passing dict as `handler` argument to async-responses would result in it being
returned as a JSON payload.

```
import aiohttp

async def test_response(ar):
    payload = {'status': 'ok'}
    ar.get('http://mock.url', '/v1/status', handler=payload)
    async with aiohttp.ClientSession() as session:
        response = await session.get('http://mock.url/v1/status')
        assert await response.json() == payload
```

### With exception as handler

Calling async-responses with an exception as `handler` argument would result in
it being raised.

```
import aiohttp
import pytest


async def test_response(ar):
    ar.get('http://mock.url', '/v1/status', handler=ZeroDivisionError)
    with pytest.raises(ZeroDivisionError):
        async with aiohttp.ClientSession() as session:
            await session.get('http://mock.url/v1/status')
```

### With string as handler

```
import aiohttp

async def test_response(ar):
    payload = 'ok'
    ar.get('http://mock.url', '/v1/status', handler=payload)
    async with aiohttp.ClientSession() as session:
        response = await session.get('http://mock.url/v1/status')
        assert await response.text() == payload
```

### With callable as handler

```
import aiohttp

async def test_response(ar):
    def handler(data, **kwargs):
        return {'status': 'ok'}

    ar.get('http://mock.url', '/v1/status', handler=payload)
    async with aiohttp.ClientSession() as session:
        response = await session.get('http://mock.url/v1/status')
        assert await response.json() == {'status': 'ok'}
```

### With a custom status code

```
import aiohttp

async def test_response(ar):
    payload = {'status': 'not good'}
    ar.get('http://mock.url', '/v1/status', handler=payload, status=500)
    async with aiohttp.ClientSession() as session:
        response = await session.get('http://mock.url/v1/status')
        assert await respose.status == 500
        assert await response.json() == payload
```

### With a custom response class

async-responses doesn't ignore arguments passed while initializing ClientSession,
including `response_class`, so you can use things like custom JSON serializer.

```
import aiohttp

async def test_response(ar):
    class CustomResponse(aiohttp.ClientResponse):
        async def json(self, *args, **kwargs):
            return {'hello': 'world'}

    ar.get('http://mock.url', '/v1/status', handler='')
    async with aiohttp.ClientSession(response_class=CustomResponse) as session:
        response = await session.get('http://mock.url/v1/status')
        assert await response.json() == {'hello': 'world'}
        assert isinstance(response, CustomResponse)
```
