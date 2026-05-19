__all__ = ["GAConfig", "GAResult", "run_genetic_algorithm"]


def __getattr__(name: str):
    if name in __all__:
        from algorithms.genetic_algorithm import (
            GAConfig,
            GAResult,
            run_genetic_algorithm,
        )

        exports = {
            "GAConfig": GAConfig,
            "GAResult": GAResult,
            "run_genetic_algorithm": run_genetic_algorithm,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
