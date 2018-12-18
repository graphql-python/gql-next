import os
import json
import requests
from graphql import get_introspection_query, build_client_schema


def load_introspection_from_server(url):
    query = get_introspection_query()
    request = requests.post(url, json={'query': query})
    if request.status_code == 200:
        return request.json()['data']
    else:
        raise Exception(f'Query failed to run by returning code of {request.status_code}. {query}')


def load_introspection_from_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)


def load_schema(uri):
    introspection = load_introspection_from_file(uri) if os.path.isfile(uri) else load_introspection_from_server(uri)
    return build_client_schema(introspection)
