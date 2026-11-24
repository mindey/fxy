import sys


def main():
    namespace = {}
    exec("from fxy.calc import *", namespace)

    if len(sys.argv) > 1:
        expression = sys.argv[1]
        try:
            result = eval(expression, namespace)
            print(result)
        except Exception as exc:
            print(f"Error evaluating expression: {exc}")
    else:
        print("Please provide a valid 'fxy' expression to evaluate.")


if __name__ == "__main__":
    main()
