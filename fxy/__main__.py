import importlib.util
import sys


def main():
    missing = [
        module
        for module in ("mpmath", "eday")
        if importlib.util.find_spec(module) is None
    ]
    if missing:
        print(
            "Calculator support is not installed "
            f"(missing: {', '.join(missing)}); install fxy[calc].",
            file=sys.stderr,
        )
        raise SystemExit(2)

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
        print("Please provide a valid fxy expression to evaluate.")


if __name__ == "__main__":
    main()
