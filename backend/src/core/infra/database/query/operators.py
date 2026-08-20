from typing import Any, Callable

from sqlalchemy import BinaryExpression, bindparam

_OPERATORS: dict[str, Callable[[Any, Any], BinaryExpression]] = {
    "eq": lambda col, val: col == val,
    "ne": lambda col, val: col != val,
    "gte": lambda col, val: col >= val,
    "lte": lambda col, val: col <= val,
    "gt": lambda col, val: col > val,
    "lt": lambda col, val: col < val,
    "in": lambda col, val: col.in_(
        bindparam(f"exp_in_{col.name}", value=tuple(val) if isinstance(val, list) else val, expanding=True)),
    "not_in": lambda col, val: ~col.in_(
        bindparam(f"exp_notin_{col.name}", value=tuple(val) if isinstance(val, list) else val, expanding=True)),
    "icontains": lambda col, val: col.ilike(f"%{val}%"),
    "has_any": lambda col, val: col.any(),
    "has_no": lambda col, val: ~col.any(),
}
