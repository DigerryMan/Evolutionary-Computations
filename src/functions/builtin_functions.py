import math

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


# ── Single-variable optimization test functions ──────────────────────────────

@FunctionRegistry.register(description="x²  (minimum at x=0)")
def x_squared(x: float) -> float:
    return x * x


@FunctionRegistry.register(description="x³ − 2x + 1")
def cubic(x: float) -> float:
    return x ** 3 - 2 * x + 1


@FunctionRegistry.register(description="sin(x)  (global min ≈ −1)")
def sine_func(x: float) -> float:
    return math.sin(x)


@FunctionRegistry.register(description="|x|  (minimum at x=0)")
def abs_func(x: float) -> float:
    return abs(x)


@FunctionRegistry.register(description="(x−3)² + 2  (minimum at x=3)")
def shifted_quadratic(x: float) -> float:
    return (x - 3) ** 2 + 2


@FunctionRegistry.register(description="x·sin(10πx) + 1  (multimodal, [−1, 2])")
def multimodal(x: float) -> float:
    return x * math.sin(10 * math.pi * x) + 1
