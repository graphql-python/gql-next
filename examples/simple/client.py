# coding: gql

# pylint:disable=no-member,unused-import
QUERY = gql"""
query HelloQuery {
  helloo(argument: "World")
}
"""
# pylint:enable=no-member,unused-import


def main():
    result = QUERY.execute()
    print(result)
    print(result.data.hello)

if __name__ == "__main__":
    main()
