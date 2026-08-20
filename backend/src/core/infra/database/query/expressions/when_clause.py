from typing import Any
from sqlalchemy import and_
from .base import BaseExpression


class When(BaseExpression):
    def __init__(self, **kwargs: Any):
        if not kwargs:
            raise ValueError("When clause must contain at least one condition")
        self.conditions_dict = kwargs

    def resolve(self, current_model: Any, operators_map: dict[str, Any] | None = None) -> Any:
        if not operators_map:
            raise ValueError("operators_map is required to resolve When clause")

        resolved_conditions = []

        for raw_path, value in self.conditions_dict.items():
            parts = raw_path.split("__")
            possible_op = parts[-1]

            if possible_op in operators_map:
                operator = possible_op
                parts.pop()
            else:
                operator = "eq"

            field_path = "__".join(parts)
            column_expression = self._resolve_path_to_expression(current_model, field_path)

            binary_expr = operators_map[operator](column_expression, value)
            resolved_conditions.append(binary_expr)

        if len(resolved_conditions) == 1:
            return resolved_conditions[0]

        return and_(*resolved_conditions)
