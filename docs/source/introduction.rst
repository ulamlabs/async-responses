Introduction
============

Async Responses is a library providing an easy way to mock aiohttp responses inspired by `aioresponses <https://github.com/pnuckowski/aioresponses>`_.

Installation
############

Library is available on PyPi, you can simply install it using ``pip``::

    $ pip install async-responses


Usage
#####

As an instance
^^^^^^^^^^^^^^

::

    ar = AsyncResponses()
    ar.get(...)

As a context manager
^^^^^^^^^^^^^^^^^^^^

::

    with AsyncResponses() as ar:
        ar.get(...)

With dict as handler
^^^^^^^^^^^^^^^^^^^^

Passing dict as ``handler`` argument to async-responses would result in it being
returned as a JSON payload.

::

    import aiohttp
    from async_responses import AsyncResponses


    async def test_response():
        ar = AsyncResponses()
        payload = {'status': 'ok'}
        ar.get('http://mock.url', '/v1/status', handler=payload)
        async with aiohttp.ClientSession() as session:
            response = await session.get('http://mock.url/v1/status')
            assert await response.json() == payload


With exception as handler
^^^^^^^^^^^^^^^^^^^^^^^^^

Calling Async Responses with an exception as ``handler`` argument would result in
it being raised.

::

    import aiohttp
    from async_responses import AsyncResponses
    import pytest


    async def test_response():
        ar = AsyncResponses()
        ar.get('http://mock.url', '/v1/status', handler=ZeroDivisionError)
        with pytest.raises(ZeroDivisionError):
            async with aiohttp.ClientSession() as session:
                await session.get('http://mock.url/v1/status')

With string as handler
^^^^^^^^^^^^^^^^^^^^^^

::

    import aiohttp
    from async_responses import AsyncResponses

    async def test_response():
        ar = AsyncResponses()
        payload = 'ok'
        ar.get('http://mock.url', '/v1/status', handler=payload)
        async with aiohttp.ClientSession() as session:
            response = await session.get('http://mock.url/v1/status')
            assert await response.text() == payload


With callable as handler
^^^^^^^^^^^^^^^^^^^^^^^^

::

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

With a custom status code
^^^^^^^^^^^^^^^^^^^^^^^^^

::

    import aiohttp
    from async_responses import AsyncResponses


    async def test_response():
        payload = {'status': 'not good'}
        ar = AsyncResponses()
        ar.get('http://mock.url', '/v1/status', handler=payload, status=500)
        async with aiohttp.ClientSession() as session:
            response = await session.get('http://mock.url/v1/status')
            assert await respose.status == 500
            assert await response.json() == payload

With a custom response class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

async-responses will make use of a response class passed as an argument to 
ClientSession, so you can use things like custom JSON serializer::

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
