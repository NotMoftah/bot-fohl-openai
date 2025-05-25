from typing import Dict, List, Any, Literal, TypedDict


class FunctionDefinition(TypedDict):
    type: Literal["function"]
    function: Dict[str, Any]


class ExternalFunctionsHandler:
    def __init__(self):
        self.functions: List[FunctionDefinition] = []

    def __repr__(self):
        functions = [function["function"]["name"] for function in self.functions]
        return f"{self.__class__.__name__}({functions})"

    def __str__(self):
        functions = [function["function"]["name"] for function in self.functions]
        return f"{self.__class__.__name__}({functions})"

    def has_function(self, name: str) -> bool:
        pass

    def call_function(self, name: str, args: object) -> str:
        pass
