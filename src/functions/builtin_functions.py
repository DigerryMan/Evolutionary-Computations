from registry.function_registry import FunctionRegistry
from functions.approximate_func import ApproximateFunc

APPROXIMATE_FUNC = ApproximateFunc()


@FunctionRegistry.register(description="Some types")
def crazy_func(a: int, b: float, c: bool, d: str) -> int:
    return a == b == c == d == APPROXIMATE_FUNC([0.1, 0.2, 0.3])


@FunctionRegistry.register(description="Multiply two numbers")
def multiply_numbers(a: float, b: float) -> float:
    return a * b + APPROXIMATE_FUNC([0.1, 0.2, 0.3])


@FunctionRegistry.register(description="Generate Fibonacci sequence")
def fibonacci() -> list[int]:
    seq = [0, 1]
    for i in range(2, 1000):
        seq.append(seq[-1] + seq[-2])
    return seq[:1000]
