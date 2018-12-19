import click
import glob
import os
from functools import partial
from os.path import join as join_paths, isfile

from gql.config import Config
from gql.query_parser import QueryParser, AnonymousQueryError, InvalidQueryError
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

    config.save('.gql.json')

    click.echo(f"Config file generated at {click.style('.gql.json', fg='bright_white')}\n\n")


@cli.command()
@click.option('-c', '--config', 'config_filename', default='.gql.json', type=click.Path(exists=True))
def run(config_filename):
    if not isfile(config_filename):
        click.echo(f'Could not find configuration file {config_filename}')

    config = Config.load(config_filename)
    schema = load_schema(config.schema)

    filenames = glob.glob(config.documents, recursive=True)

    query_parser = QueryParser(schema)
    query_renderer = DataclassesRenderer(schema, config)

    for filename in filenames:
        root, ext = os.path.splitext(filename)
        target_filename = root + '.py'

        click.echo(f'Parsing {filename} ... ', nl=False)
        with open(filename, 'r') as fin:
            query = fin.read()
            try:
                parsed = query_parser.parse(query)
                rendered = query_renderer.render(parsed)
            except AnonymousQueryError:
                click.secho('Failed!', fg='bright_red')
                click.secho('\tQuery is missing a name', fg='bright_black')
            except InvalidQueryError as invalid_err:
                click.secho('Failed!', fg='bright_red')
                click.secho(f'\t{invalid_err}', fg='bright_black')

            with open(target_filename, 'w') as outfile:
                outfile.write(rendered)
                click.secho('Success!', fg='bright_white')


if __name__ == '__main__':
    cli()
