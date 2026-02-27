"""Function registry with decorator-based registration."""

import inspect
from typing import Any, Callable, get_type_hints

from registry.parameter_info import FunctionMetadata, ParameterInfo


class FunctionRegistry:
    """Registry for managing and executing registered functions."""

    _registry: dict[str, FunctionMetadata] = {}

    @classmethod
    def register(cls, description: str = ""):
        """Decorator to register a function.

        Usage:
            @FunctionRegistry.register(description="Add two numbers")
            def add(a: int, b: int) -> int:
                return a + b
        """

        def decorator(func: Callable) -> Callable:
            # Extract function signature and type hints
            sig = inspect.signature(func)
            try:
                hints = get_type_hints(func)
            except (NameError, AttributeError):
                # Handle cases where type hints reference undefined types
                hints = {}

            # Build parameter list
            parameters = []
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue

                param_type = hints.get(param_name, str)
                has_default = param.default != inspect.Parameter.empty

                param_info = ParameterInfo(
                    name=param_name,
                    param_type=param_type,
                    default_value=param.default if has_default else None,
                    is_optional=has_default,
                    description="",
                )
                parameters.append(param_info)

            # Create and store metadata
            metadata = FunctionMetadata(
                func_name=func.__name__,
                description=description,
                parameters=parameters,
                func=func,
            )
            cls._registry[func.__name__] = metadata

            return func

        return decorator

    @classmethod
    def get_all(cls) -> dict[str, FunctionMetadata]:
        """Get all registered functions."""
        return cls._registry.copy()

    @classmethod
    def get(cls, func_name: str) -> FunctionMetadata | None:
        """Get metadata for a specific function."""
        return cls._registry.get(func_name)

    @classmethod
    def execute(cls, func_name: str, **kwargs) -> tuple[bool, Any]:
        """Execute a registered function with error handling.

        Returns:
            (success, result) tuple where success is bool and result is the return value or error message
        """
        try:
            metadata = cls._registry.get(func_name)
            if not metadata:
                return False, f"Function '{func_name}' not found in registry"

            # Validate parameter count and types
            func_params = {p.name: p for p in metadata.parameters}
            provided_keys = set(kwargs.keys())
            required_keys = {p.name for p in metadata.parameters if not p.is_optional}

            # Check for missing required parameters
            missing = required_keys - provided_keys
            if missing:
                return (
                    False,
                    f"Missing required parameter(s): {', '.join(sorted(missing))}",
                )

            # Check for unexpected parameters
            unexpected = provided_keys - set(func_params.keys())
            if unexpected:
                return (
                    False,
                    f"Unexpected parameter(s): {', '.join(sorted(unexpected))}",
                )

            # Execute the function
            result = metadata.func(**kwargs)
            return True, result

        except TypeError as e:
            return False, f"Invalid parameters: {e}"
        except Exception as e:
            return False, f"Execution error: {type(e).__name__}: {e}"
