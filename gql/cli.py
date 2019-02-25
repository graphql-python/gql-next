#!/usr/bin/env python
import click
import glob
import time
import os
from os.path import join as join_paths, isfile

from graphql import GraphQLSchema
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, EVENT_TYPE_CREATED, EVENT_TYPE_MODIFIED

from gql.config import Config
from gql.query_parser import QueryParser, AnonymousQueryError, InvalidQueryError
from gql.renderer_dataclasses import DataclassesRenderer
from gql.utils_schema import load_schema

DEFAULT_CONFIG_FNAME = '.gql.json'
SCHEMA_PROMPT = click.style('Where is your schema?: ', fg='bright_white') + \
                click.style('(path or url) ', fg='bright_black', dim=False)

ROOT_PROMPT = click.style('Whats the root of your project: ', fg='bright_white') + \
              click.style('(path or url) ', fg='bright_black', dim=False)


def safe_remove(fname):
    try:
        os.remove(fname)
    except:
        pass


@click.group()
def cli():
    pass


@cli.command()
@click.option('--schema', prompt=SCHEMA_PROMPT, default='http://localhost:4000')
@click.option('--endpoint', prompt=SCHEMA_PROMPT, default='same as schema')
@click.option('--root', prompt=ROOT_PROMPT, default='./src')
@click.option('-c', '--config', 'config_filename', default=DEFAULT_CONFIG_FNAME, type=click.Path(exists=False))
def init(schema, endpoint, root, config_filename):
    if isfile(config_filename):
        click.confirm(f'{config_filename} already exists. Are you sure you want to continue?', abort=True)

    if endpoint == 'same as schema':
        endpoint = schema

    config = Config(
        schema=schema,
        endpoint=endpoint,
        documents=join_paths(root, '**/*.graphql')
    )

    config.save(config_filename)

    click.echo(f"Config file generated at {click.style(config_filename, fg='bright_white')}\n\n")


def process_file(filename: str, parser: QueryParser, renderer: DataclassesRenderer):
    root, _s = os.path.splitext(filename)
    target_filename = root + '.py'

    click.echo(f'Parsing {filename} ... ', nl=False)
    with open(filename, 'r') as fin:
        query = fin.read()
        try:
            parsed = parser.parse(query)
            rendered = renderer.render(parsed)
            with open(target_filename, 'w') as outfile:
                outfile.write(rendered)
                click.secho('Success!', fg='bright_white')

        except AnonymousQueryError:
            click.secho('Failed!', fg='bright_red')
            click.secho('\tQuery is missing a name', fg='bright_black')
            safe_remove(target_filename)
        except InvalidQueryError as invalid_err:
            click.secho('Failed!', fg='bright_red')
            click.secho(f'\t{invalid_err}', fg='bright_black')
            safe_remove(target_filename)


@cli.command()
@click.option('-c', '--config', 'config_filename', default=DEFAULT_CONFIG_FNAME, type=click.Path(exists=True))
def run(config_filename):
    if not isfile(config_filename):
        click.echo(f'Could not find configuration file {config_filename}')

    config = Config.load(config_filename)
    schema = load_schema(config.schema)

    filenames = glob.glob(config.documents, recursive=True)

    query_parser = QueryParser(schema)
    query_renderer = DataclassesRenderer(schema, config)

    for filename in filenames:
        process_file(filename, query_parser, query_renderer)


@cli.command()
@click.option('-c', '--config', 'config_filename', default=DEFAULT_CONFIG_FNAME, type=click.Path(exists=True))
def watch(config_filename):
    class Handler(FileSystemEventHandler):
        def __init__(self, config: Config, schema: GraphQLSchema):
            self.parser = QueryParser(schema)
            self.renderer = DataclassesRenderer(schema, config)

        def on_any_event(self, event):
            if event.is_directory:
                return

            if event.event_type in {EVENT_TYPE_CREATED, EVENT_TYPE_MODIFIED}:
                filenames = [os.path.abspath(fn) for fn in glob.iglob(config.documents, recursive=True)]
                if event.src_path not in filenames:
                    return

                # Take any action here when a file is first created.
                process_file(event.src_path, self.parser, self.renderer)

    if not isfile(config_filename):
        click.echo(f'Could not find configuration file {config_filename}')

    config = Config.load(config_filename)
    schema = load_schema(config.schema)

    click.secho(f'Watching {config.documents}', fg='cyan')
    click.secho('Ready for changes...', fg='cyan')

    observer = Observer()
    observer.schedule(Handler(config, schema), os.path.abspath('./'), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(5)
    except:
        observer.stop()
        print('Error')

    observer.join()


if __name__ == '__main__':
    cli()
