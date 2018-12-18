from typing import Callable, Mapping

import requests


class Client:
    def __init__(self, endpoint, headers=None):
        self.endpoint = endpoint

        headers = headers or {}
        self.__headers = {
            **headers,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
        }

    async def call(self, query,
                   variables=None,
                   on_before_callback: Callable[[Mapping[str, str], Mapping[str, str]], None] = None) -> dict:

        headers = self.__headers.copy()

        payload = {
            'query': query
        }
        if variables:
            payload['variables'] = variables

        if on_before_callback:
            on_before_callback(payload, headers)

        response = requests.post(self.endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
