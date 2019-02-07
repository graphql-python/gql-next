# coding: gql

# pylint:disable=no-member,unused-import
QUERY = gql"""
query HelloQuery {
  hello(argument: "World")
}
"""
# pylint:enable=no-member,unused-import

def main():
    result = QUERY.execute()
    print(result)

if __name__ == "__main__":
    main()
