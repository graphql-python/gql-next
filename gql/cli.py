import click
import yaml
from os.path import join as join_paths, isfile

SCHEMA_PROMPT = click.style('Where is your schema?: ', fg='bright_white') + \
                click.style('(path or url) ', fg='bright_black', dim=False)

ROOT_PROMPT = click.style('Whats the root of your project: ', fg='bright_white') + \
              click.style('(path or url) ', fg='bright_black', dim=False)


@click.group()
def cli():
    pass

@cli.command()
@click.option('--schema', prompt=SCHEMA_PROMPT, default="http://localhost:4000")
@click.option('--root', prompt=ROOT_PROMPT, default="./src")
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


if __name__ == '__main__':
    cli()
