from typing import Dict, List, Any, Literal, TypedDict


class FunctionTool(TypedDict):
    type: Literal["function"]
    function: Dict[str, Any]


class ExternalToolsHandler:
    def __init__(self):
        self.tools: List[FunctionTool] = []

    def __repr__(self):
        functions = [tool["function"]["name"] for tool in self.tools]
        return f"{self.__class__.__name__}({functions})"

    def __str__(self):
        functions = [tool["function"]["name"] for tool in self.tools]
        return f"{self.__class__.__name__}({functions})"

    def has_function(self, name: str) -> bool:
        pass

    def call_function(self, name: str, args: object) -> str:
        pass
