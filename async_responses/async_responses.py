from typing import Callable, Union, List, Tuple
from dataclasses import dataclass
from unittest import mock

from aiohttp import (
    ClientSession, ClientResponse, StreamReader, ClientConnectionError
)
from aiohttp.client_proto import ResponseHandler
from aiohttp.helpers import TimerNoop, URL
from multidict import CIMultiDict, CIMultiDictProxy


# Alias for everything that can be a handler
AsyncResponsesHandler = Union[Callable, dict, str, Exception]


@dataclass
class Response:
    method: str
    hostname: str
    path: str
    handler: AsyncResponsesHandler
    status: int


@dataclass
class Call:
    method: str
    url: str
    args: tuple
    kwargs: dict


class AsyncResponses:
    """
    Async Responses context manager

    :param passthrough: list of patterns of URLs which won't be mocked
    :param mock_module: mock module, defaults to unittest.mock
    """

    def __init__(self, *, mock_module=None, passthrough=[]):
        self._responses = []
        self._calls = []
        self._passthrough = passthrough
        self.mock_module = mock_module or mock
        self.mock = self.mock_module.patch(
            'aiohttp.client.ClientSession._request',
            side_effect=self.handle,
            autospec=True,
        )
        self.mock.start()

    def __enter__(self) -> 'AsyncResponses':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mock.stop()
        self.reset()

    @property
    def calls(self) -> List['Call']:
        """List of calls"""
        return self._calls

    @property
    def responses(self) -> List['Response']:
        """List of responses"""
        return self._responses

    def add(
        self, method: str, hostname: str, path: str,
        handler: AsyncResponsesHandler, status: int = 200
    ):
        """
        Mocks aiohttp response for the next request matching parameters.

        :param method: HTTP method, for example ``get``
        :param hostname: server hostname
        :param path: path
        :param handler: response, can be either a dict, string, callable or
                        an exception
        :param status: status code, defaults to 200
        """
        if not path.startswith('/'):
            path = f'/{path}'
        self._responses.append(
            Response(method, hostname, path, handler, status)
        )

    def patch(
        self, hostname: str, path: str,
        handler: AsyncResponsesHandler, status: int = 200
    ) -> None:
        """Mocks PATCH request. Shorthand for ``add('patch', *args)``"""
        self.add('patch', hostname, path, handler, status)

    def post(
        self, hostname: str, path: str,
        handler: AsyncResponsesHandler, status: int = 200
    ) -> None:
        """Mocks POST request. Shorthand for ``add('post', *args)``"""
        self.add('post', hostname, path, handler, status)

    def put(
        self, hostname: str, path: str,
        handler: AsyncResponsesHandler, status: int = 200
    ) -> None:
        """Mocks PUT request. Shorthand for ``add('put', *args)``"""
        self.add('put', hostname, path, handler, status)

    def get(
        self, hostname: str, path: str,
        handler: AsyncResponsesHandler, status: int = 200
    ) -> None:
        """Mocks GET request. Shorthand for ``add('get', *args)``"""
        self.add('get', hostname, path, handler, status)

    def reset(self) -> None:
        """Resets mock"""
        self._responses.clear()
        self._calls.clear()

    def passthrough(self, pattern: str) -> None:
        """
        Adds passthrough. Requests to URLs which match the pattern won't be
        mocked.
        """
        self._passthrough.append(pattern)

    async def handle(
            self, orig_self, method, url, *args, **kwargs
    ) -> Union[ClientResponse, Exception]:
        url = str(url)
        if self.is_passthrough(url):
            return await self.mock.temp_original(
                orig_self, method, url, *args, **kwargs
            )

        self._calls.append(Call(method, url, args, kwargs))
        handler, status = self.match(method, url)

        if 'json' in kwargs:
            self.try_to_serialize(kwargs['json'], orig_self._json_serialize)

        # check response status
        raise_for_status = kwargs.get('raise_for_status')
        if raise_for_status is None:
            raise_for_status = orig_self._raise_for_status

        payload = handler(*args, **kwargs) if callable(handler) else handler
        if isinstance(payload, Exception):
            if not raise_for_status:
                raise payload
            else:
                status = 500
                payload = {'error': 'Internal Server Error'}

        if isinstance(payload, dict):
            payload = orig_self._json_serialize(payload)

        # At this point, payload should be a string
        assert isinstance(payload, str)
        resp = self.build_response(
            method,
            url,
            payload,
            session=orig_self,
            status=status
        )

        if callable(raise_for_status):
            await raise_for_status(resp)
        elif raise_for_status:
            resp.raise_for_status()

        return resp

    def is_passthrough(self, url):
        return any(pattern in url for pattern in self._passthrough)

    def match(self, method: str, url: str) -> Tuple[Callable[..., dict], int]:
        try:
            i, handler, status = next(
                (i, r.handler, r.status)
                for i, r in enumerate(self._responses)
                if r.method.lower() == method.lower()
                and url == f'{r.hostname}{r.path}'
            )
            del self._responses[i]
            return handler, status
        except StopIteration:
            raise ClientConnectionError(f'No response for {method} {url}')

    def try_to_serialize(self, body, json_serialize):
        try:
            json_serialize(body)
        except TypeError as e:
            raise ValueError('body not serializable') from e

    def build_response(
        self,
        method: str,
        url: str,
        payload: str,
        *,
        session: ClientSession,
        status: int
    ) -> ClientResponse:
        response = session._response_class(
            method,
            URL(url),
            request_info=self.mock_module.Mock(),
            writer=self.mock_module.Mock(),
            continue100=None,
            timer=TimerNoop(),
            traces=[],
            loop=session.loop,
            session=session
        )
        response._headers = CIMultiDictProxy(
            CIMultiDict({'Content-Type': 'application/json'})
        )
        response.status = status
        if status >= 400:
            response.reason = payload

        response.content = StreamReader(ResponseHandler(session.loop))
        response.content.feed_data(str.encode(payload))
        response.content.feed_eof()
        return response
