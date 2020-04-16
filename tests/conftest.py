import aiohttp
import pytest

from async_responses import AsyncResponses


@pytest.fixture(autouse=True)
async def _loop(loop):
    return loop


@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
def ar(request):
    params = request.node.get_closest_marker('ar')
    kwargs = params.kwargs if params else {}

    with AsyncResponses(**kwargs) as m:
        yield m
