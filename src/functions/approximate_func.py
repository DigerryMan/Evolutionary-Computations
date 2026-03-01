import benchmark_functions as bf


class ApproximateFunc:
    def __init__(self, func: bf.BenchmarkFunction = bf.Hypersphere(n_dimensions=3)):
        self.func = func
        self.range = func.suggested_bounds()
        print(
            f"Benchmark function: {self.func.name()}\nRange: {self.range}\nGlobal minimum to be found: {self.func.minimum()}"
        )

    def __call__(self, x: list) -> float:
        return self.func(x)
