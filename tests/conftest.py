import aiohttp
import pytest

from async_responses import AsyncResponses


@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
def ar(request, mocker, loop):
    params = request.node.get_closest_marker('ar')
    kwargs = params.kwargs if params else {}

    with AsyncResponses(mocker.mock_module, loop, **kwargs) as m:
        yield m
