# Async Responses

[![Documentation Status](https://readthedocs.org/projects/async-responses/badge/?version=latest)](http://async-responses.readthedocs.io/en/latest/?badge=latest) [![codecov](https://codecov.io/gh/ulamlabs/async-responses/branch/master/graph/badge.svg)](https://codecov.io/gh/ulamlabs/async-responses) ![Python package](https://github.com/ulamlabs/async-responses/workflows/Python%20package/badge.svg) ![Upload Python Package](https://github.com/ulamlabs/async-responses/workflows/Upload%20Python%20Package/badge.svg)

Async Responses is a library providing an easy way to mock aiohttp responses inspired by [aioresponses](https://github.com/pnuckowski/aioresponses).

## Installation

Library is available on PyPi, you can simply install it using `pip`.

```shell
$ pip install async-responses
```

## Usage
### As an instance
```python
ar = AsyncResponses()
ar.get(...)
```

### As a context manager
```python
with AsyncResponses() as ar:
    ar.get(...)
```

### With dict as handler
Passing dict as `handler` argument to async-responses would result in it being
returned as a JSON payload.

```python
import aiohttp
from async_responses import AsyncResponses


async def test_response():
    ar = AsyncResponses()
    payload = {'status': 'ok'}
    ar.get('http://mock.url', '/v1/status', handler=payload)
    async with aiohttp.ClientSession() as session:
        response = await session.get('http://mock.url/v1/status')
        assert await response.json() == payload
```

### With exception as handler
Calling Async Responses with an exception as `handler` argument would result in
it being raised.

```python
import aiohttp
from async_responses import AsyncResponses
import pytest


async def test_response():
    ar = AsyncResponses()
    ar.get('http://mock.url', '/v1/status', handler=ZeroDivisionError)
    with pytest.raises(ZeroDivisionError):
        async with aiohttp.ClientSession() as session:
            await session.get('http://mock.url/v1/status')
```

### With string as handler
```python
import aiohttp
from async_responses import AsyncResponses

async def test_response():
    ar = AsyncResponses()
    payload = 'ok'
    ar.get('http://mock.url', '/v1/status', handler=payload)
    async with aiohttp.ClientSession() as session:
        response = await session.get('http://mock.url/v1/status')
        assert await response.text() == payload
```

### With callable as handler
```python
import aiohttp
from async_responses import AsyncResponses


async def test_response():
    def handler(data, **kwargs):
        return {'status': 'ok'}

    ar = AsyncResponses()
    ar.get('http://mock.url', '/v1/status', handler=payload)
    async with aiohttp.ClientSession() as session:
        response = await session.get('http://mock.url/v1/status')
        assert await response.json() == {'status': 'ok'}
```

### With a custom status code
```python
import aiohttp
from async_responses import AsyncResponses


async def test_response():
    payload = {'status': 'not good'}
    ar = AsyncResponses()
    ar.get('http://mock.url', '/v1/status', handler=payload, status=500)
    async with aiohttp.ClientSession() as session:
        response = await session.get('http://mock.url/v1/status')
        assert response.status == 500
        assert await response.json() == payload
```

### With a custom response class
async-responses will make use of a response class passed as an argument to 
ClientSession, so you can use things like custom JSON serializer.

```python
import aiohttp

async def test_response():
    class CustomResponse(aiohttp.ClientResponse):
        async def json(self, *args, **kwargs):
            return {'hello': 'world'}

    ar = AsyncResponses()
    ar.get('http://mock.url', '/v1/status', handler='')
    async with aiohttp.ClientSession(response_class=CustomResponse) as session:
        response = await session.get('http://mock.url/v1/status')
        assert await response.json() == {'hello': 'world'}
        assert isinstance(response, CustomResponse)
```
