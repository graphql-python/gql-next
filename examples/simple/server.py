import graphene
from flask_graphql import GraphQLView
from flask import Flask

class Query(graphene.ObjectType):
    # pylint:disable=no-self-use
    hello = graphene.String(argument=graphene.String(default_value="stranger"))

    def resolve_hello(self, _, argument):
        return 'Hello ' + argument

SCHEMA = graphene.Schema(query=Query)


APP = Flask(__name__)
APP.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=SCHEMA, graphiql=True))
