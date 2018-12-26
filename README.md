# GQL: Python GraphQL Client Library

[![Build Status](https://travis-ci.org/ekampf/cql.svg?branch=master)](https://travis-ci.org/ekampf/cql)
[![Coverage Status](https://coveralls.io/repos/github/ekampf/gql/badge.svg?branch=master)](https://coveralls.io/github/ekampf/gql?branch=master)

Work in progress!  Do NOT use yet...

## Introduction

GQL is a GraphQL Client Python library intended to help Python application make GraphQL
API call while enjoying the advantages that come with GraphQL.

- **Strongly Typed** response objects (dynamically created in build time to match your query)
- **Query Validation** that checks your code's queries against the GraphQL server's schema.

## Installation

Simply install from PyPi:

```bash
pip install !!TBD!!
```

Then go to your project folder and run `gql init`


## How it works


### The `gql` client

#### `gql init`
Initializes a project to use GQL as client - writes a .gql.json configuration file.

#### `gql run`

Run through your project's files and compile GraphQL queries into into Python types.

#### `gql watch`

Useful during development. Listen to file changes in your project's folder and continuously
builds GraphQL queries as they change.
This allows you to:
* Immediately verify query changes you make are valid.
* Enjoy your IDE's autocomplete features on GraphQL auto-generated objects while developing
as `watch` will auto-update them as you change queries.
