import codecs


def search_function(encoding):
    if encoding not in ('gql', 'graphql', 'pygql'):
        return None

    import gql.codec.register
    return gql.codec.register.search_function(encoding)


codecs.register(search_function)
