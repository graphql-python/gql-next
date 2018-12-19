
.PHONY: deps lint test build

lint:
	@poetry run pylint ./gql --output-format=parseable

test:
	@poetry run pytest --cov=gql --color=yes --show-capture=no

build:
	@poetry build
