import click
from os.path import join as join_paths, isfile

from gql.config import Config
from gql.query_parser import QueryParser
from gql.renderer_dataclasses import DataclassesRenderer
from gql.utils_schema import load_schema

SCHEMA_PROMPT = click.style('Where is your schema?: ', fg='bright_white') + \
                click.style('(path or url) ', fg='bright_black', dim=False)

ROOT_PROMPT = click.style('Whats the root of your project: ', fg='bright_white') + \
              click.style('(path or url) ', fg='bright_black', dim=False)


@click.group()
def cli():
    pass

@cli.command()
@click.option('--schema', prompt=SCHEMA_PROMPT, default='http://localhost:4000')
@click.option('--root', prompt=ROOT_PROMPT, default='./src')
def init(schema, root):
    if isfile('gql.yml'):
        click.confirm('gql.yml already exists. Are you sure you want to continue?', abort=True)

    documents = join_paths(root, '**/*.graphql')
    config = Config(
        schema=schema,
        documents=documents
    )

    with open('gql.yml', 'w') as outfile:
        yaml.dump(config, outfile, default_flow_style=False)

    click.echo(f"Config file generated at {click.style('gql.yml', fg='bright_white')}\n\n")


@cli.command()
@click.option('-c', '--config', 'config_filename', default='gql.yml', type=click.Path(exists=True))
def run(config_filename):
    if not isfile(config_filename):
        click.echo(f'Could not find configuration file {config_filename}')

    config = Config.load(config_filename)

    schema = load_schema(config.schema)

    query = """
    query MyQuery {
      products: snapshots(app: EDC, snapshotType: PRODUCT) {
        pageInfo {
          endCursor
          hasNextPage
        }
        edges {
          node {
            ... on Product {
              id
              name
            }
          }
        }
      }
    }
    """

    query_parser = QueryParser(schema)
    query_renderer = DataclassesRenderer(schema)

    parsed = query_parser.parse(query)
    print(query_renderer.render(parsed))


if __name__ == '__main__':
    cli()
