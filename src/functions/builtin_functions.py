from registry.function_registry import FunctionRegistry


@FunctionRegistry.register(description="Some types")
def crazy_func(a: int, b: float, c: bool, d: str) -> int:
    return a == b == c == d


@FunctionRegistry.register(description="Multiply two numbers")
def multiply_numbers(a: float, b: float) -> float:
    return a * b


@FunctionRegistry.register(description="Generate Fibonacci sequence")
def fibonacci() -> list[int]:
    seq = [0, 1]
    for i in range(2, 1000):
        seq.append(seq[-1] + seq[-2])
    return seq[:1000]
