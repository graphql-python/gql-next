import click
import yaml
import json
from jinja2 import Environment, FileSystemLoader
from os.path import join as join_paths, isfile, dirname

from graphql import GraphQLEnumType, GraphQLObjectType, GraphQLNonNull

from gql.query_parser import QueryParser
from gql.utils_schema import load_schema

SCHEMA_PROMPT = click.style('Where is your schema?: ', fg='bright_white') + \
                click.style('(path or url) ', fg='bright_black', dim=False)

ROOT_PROMPT = click.style('Whats the root of your project: ', fg='bright_white') + \
              click.style('(path or url) ', fg='bright_black', dim=False)


def render(schema):
    def type_to_python(scalar):
        nullable = True
        if isinstance(scalar, GraphQLNonNull):
            nullable = False
            scalar = scalar.of_type

        mapping = {
            'String': 'str',
            'Int': 'int',
            'Float': 'float',
            'Boolean': 'bool',
            'DateTime': 'str'  # TODO: ?
        }

        mapping = mapping.get(str(scalar), scalar)
        return mapping if not nullable else f'{mapping} = None'

    env = Environment(
        loader=FileSystemLoader(join_paths(dirname(__file__), 'templates')),
        trim_blocks=True,
        lstrip_blocks=True
    )
    env.filters['jsonify'] = json.dumps
    env.globals.update(type_to_python=type_to_python)

    template = env.get_template('root.j2')

    enums = {k: v for k, v in schema.type_map.items() if isinstance(v, GraphQLEnumType) and not k.startswith('__')}
    types = {k: v for k, v in schema.type_map.items() if isinstance(v, GraphQLObjectType) and not k.startswith('__')}

    template_vars = {
        'schema': schema,
        'enums': enums,
        'types': types
    }
    output = template.render(template_vars)
    return output


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
    config = dict(
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

    with open(config_filename, 'r') as f:
        config = yaml.load(f)

    schema = load_schema(config['schema'])
    # print(schema.type_map)
    # print(render(schema))

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
    print(query_parser.parse(query))


if __name__ == '__main__':
    cli()
