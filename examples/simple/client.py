# coding: gql

MY_QUERY = gql"""
query hello_query {
  hello(argument: "World")
}
"""

def main():
    result = MY_QUERY.execute()
    print(result)

if __name__ == "__main__":
    main()