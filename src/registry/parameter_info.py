from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ParameterInfo:
    name: str
    param_type: type
    default_value: Any
    is_optional: bool
    description: str = ""


@dataclass
class FunctionMetadata:
    func_name: str
    description: str
    parameters: list[ParameterInfo]
    func: Callable
