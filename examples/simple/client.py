# coding: gql

QUERY = gql"""
query HelloQuery {
  hello(argument: "World")
}
"""

def main():
    result = QUERY.execute()
    print(result)

if __name__ == "__main__":
    main()
