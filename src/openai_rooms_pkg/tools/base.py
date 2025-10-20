# FILE: src/openai_rooms_pkg/tools/base.py
from typing import Any, Callable


class ToolRegistry:
    """
    Minimal tool registry compatible with the working Anthropic addon.
    It lets the engine register external tool functions and pass their
    JSON Schemas to actions that support tools.
    """

    def __init__(self):
        self.functions: dict[str, Callable] = {}
        self.tool_definitions: dict[str, dict[str, Any]] = {}
        self.tool_max_retries: dict[str, int] = {}

    def register_tools(
        self,
        tool_functions: dict[str, Callable],
        tool_descriptions: dict[str, str] | None = None,
        tool_max_retries: dict[str, int] | None = None,
    ):
        tool_descriptions = tool_descriptions or {}
        tool_max_retries = tool_max_retries or {}

        for action_name, func in tool_functions.items():
            desc = tool_descriptions.get(action_name)
            if not desc:
                if "::" in action_name:
                    addon_name = action_name.split("::", 1)[0]
                    desc = f"Execute {action_name.split('::')[-1]} action from {addon_name} addon"
                else:
                    desc = f"Execute {action_name} action"
            self.tool_max_retries[action_name] = tool_max_retries.get(action_name, 0)
            self._register_single_tool(action_name, func, desc)

    def _register_single_tool(self, action_name: str, func: Callable, description: str):
        self.functions[action_name] = func
        self.tool_definitions[action_name] = {
            "name": action_name,
            "description": description or f"Execute {action_name} action",
            "input_schema": self._convert_annotations_to_schema(func),
        }

    def _convert_annotations_to_schema(self, func: Callable) -> dict[str, Any]:
        try:
            import inspect

            from pydantic import create_model

            sig = inspect.signature(func)
            if not sig.parameters:
                return {"type": "object", "properties": {}, "required": []}

            fields = {}
            for pname, param in sig.parameters.items():
                ann = param.annotation if param.annotation is not inspect._empty else Any
                default = ... if param.default is inspect._empty else param.default
                fields[pname] = (ann, default)

            DynamicModel = create_model("DynamicToolSchema", **fields)
            schema = DynamicModel.model_json_schema()

            schema.setdefault("properties", {})
            schema.setdefault("required", [])
            schema.setdefault("type", "object")
            return schema
        except Exception:
            # Fallback very permissive schema
            return {"type": "object", "properties": {}, "required": []}

    def get_tools_for_action(self) -> dict[str, Any]:
        return self.tool_definitions.copy()

    def get_function(self, action_name: str) -> Callable | None:
        return self.functions.get(action_name)

    def get_max_retries(self, action_name: str) -> int:
        return self.tool_max_retries.get(action_name, 0)

    def clear(self):
        self.functions.clear()
        self.tool_definitions.clear()
        self.tool_max_retries.clear()
