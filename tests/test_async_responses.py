import json
import uuid

import aiohttp
import pytest


HOSTNAME, PATH = 'https://test.ar', 'index'


async def test_match_request(ar, session):
    ar.get(HOSTNAME, PATH, handler={})
    try:
        await session.get(f'{HOSTNAME}/{PATH}')
    except aiohttp.ClientConnectionError as e:
        pytest.fail(f'Should not have returned {e}', pytrace=True)


async def test_no_match(ar, session):
    with pytest.raises(aiohttp.ClientConnectionError):
        await session.get(f'{HOSTNAME}/{PATH}')


async def test_response_single_use(ar, session):
    ar.get(HOSTNAME, PATH, handler={})
    await session.get(f'{HOSTNAME}/{PATH}')
    with pytest.raises(aiohttp.ClientConnectionError):
        await session.get(f'{HOSTNAME}{PATH}')


async def test_post_reponse(ar, session):
    ar.post(HOSTNAME, PATH, handler={})
    try:
        await session.post(f'{HOSTNAME}/{PATH}')
    except aiohttp.ClientConnectionError as e:
        pytest.fail(f'Should not have returned {e}', pytrace=True)


async def test_get_response(ar, session):
    ar.get(HOSTNAME, PATH, handler={})
    try:
        await session.get(f'{HOSTNAME}/{PATH}')
    except aiohttp.ClientConnectionError as e:
        pytest.fail(f'Should not have returned {e}', pytrace=True)


async def test_dict_handler(ar, session):
    payload = {'test': 'test'}
    ar.get(HOSTNAME, PATH, handler=payload)
    resp = await session.get(f'{HOSTNAME}/{PATH}')
    json = await resp.json()
    assert json == payload


async def test_callable_handler(ar, session):
    def handler(data, **kwargs):
        return kwargs
    kwargs = {'json': '{"key": "val"}'}
    ar.post(HOSTNAME, PATH, handler=handler)
    resp = await session.post(f'{HOSTNAME}/{PATH}', **kwargs)
    json = await resp.json()
    assert json == kwargs


async def test_str_handler(ar, session):
    ar.get(HOSTNAME, PATH, handler='test')
    response = await session.get(f'{HOSTNAME}/{PATH}')
    with pytest.raises(json.JSONDecodeError):
        await response.json()


async def test_body_not_serializable(ar, session):
    with pytest.raises(ValueError):
        ar.post(HOSTNAME, PATH, handler={})
        await session.post(f'{HOSTNAME}/{PATH}', json={'id': uuid.uuid4()})


async def test_exception_handler(ar, session):
    with pytest.raises(ZeroDivisionError):
        ar.get(HOSTNAME, PATH, handler=ZeroDivisionError())
        await session.get(f'{HOSTNAME}/{PATH}')


async def test_raise_for_status(ar, session):
    ar.get(HOSTNAME, PATH, handler={'test': 'test'}, status=500)
    with pytest.raises(aiohttp.ClientResponseError):
        await session.get(f'{HOSTNAME}/{PATH}', raise_for_status=True)

    ar.get(HOSTNAME, PATH, handler=ZeroDivisionError())
    with pytest.raises(aiohttp.ClientResponseError):
        await session.get(f'{HOSTNAME}/{PATH}', raise_for_status=True)


async def test_preserve_response_class(ar):
    class CustomResponse(aiohttp.ClientResponse):
        async def json(self, *args, **kwargs):
            return {'hello': 'world'}

    ar.get(HOSTNAME, PATH, handler={})
    async with aiohttp.ClientSession(response_class=CustomResponse) as session:
        response = await session.get(f'{HOSTNAME}/{PATH}')
        assert await response.json() == {'hello': 'world'}
        assert isinstance(response, CustomResponse)
