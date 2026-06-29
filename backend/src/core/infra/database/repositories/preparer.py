from typing import Any, Callable, Generic, Sequence, Type, Union

from sqlalchemy import BinaryExpression
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.interfaces import ORMOption

from src.core.annotations import ORM_MODEL_T
from src.core.infra.database.query_modifiers import BaseQueryModifier


class QueryPreparer(Generic[ORM_MODEL_T]):
    model: Type[ORM_MODEL_T]

    _OPERATORS: dict[str, Callable[[Any, Any], BinaryExpression]] = {
        "eq": lambda col, val: col == val,
        "ne": lambda col, val: col != val,
        "gte": lambda col, val: col >= val,
        "lte": lambda col, val: col <= val,
        "gt": lambda col, val: col > val,
        "lt": lambda col, val: col < val,
        "in": lambda col, val: col.in_(val),
        "ilike": lambda col, val: col.ilike(f"%{val}%"),
        "has_any": lambda col, val: col.any(),
        "has_no": lambda col, val: ~col.any(),
    }

    def _prepare_query(
            self,
            *,
            order_by: str | None = None,
            options: Sequence[Any] | None = None,
            with_for_update: bool | dict[str, Any] = False,
            **kwargs: Any,
    ) -> tuple[Any, list[BaseQueryModifier]]:
        from sqlalchemy import select
        q = select(self.model)
        orm_options = []
        modifiers: list[BaseQueryModifier] = []

        if options is not None:
            for opt in options:
                if isinstance(opt, BaseQueryModifier):
                    modifiers.append(opt)
                else:
                    orm_options.append(opt)

        if orm_options:
            q = q.options(*orm_options)

        for modifier in modifiers:
            q = modifier.apply_to_query(q, self.model)

        if with_for_update:
            if isinstance(with_for_update, dict):
                q = q.with_for_update(**with_for_update)
            else:
                q = q.with_for_update()

        if kwargs:
            q = self._build_filtered_query(q, kwargs)

        if order_by:
            q = self._apply_sorting(q, order_by)

        return q, modifiers

    def _process_results(self, rows: Sequence[Any], modifiers: list[BaseQueryModifier]) -> Any:
        if not rows:
            return rows
        is_sequence = isinstance(rows, (list, tuple, Sequence)) and not (
                isinstance(rows, tuple) and hasattr(rows, "_mapping"))
        instances = list(rows) if is_sequence else [rows]

        if modifiers:
            for modifier in modifiers:
                modifier.process_results(instances, self.model)

        cleaned = [row if isinstance(row, tuple) and len(row) > 0 else row for row in instances]
        return cleaned if is_sequence else cleaned[0]

    def _build_filtered_query(self, query: Any, filters: dict[str, Any]) -> Any:
        joined_models = set()
        for key, value in filters.items():
            if value is not None:
                query = self._apply_filter(query, key, value, joined_models)
        return query

    def _apply_filter(self, query: Any, key: str, value: Any, joined_models: set) -> Any:
        path, operator = key.split("__", 1) if "__" in key else (key, "eq")
        if operator in self._OPERATORS:
            pass
        else:
            path = key
            operator = "eq"

        parts = path.split("__")
        field_name = parts.pop()
        current_model = self.model
        eager_option = None

        for relation_name in parts:
            if hasattr(current_model, relation_name):
                relation_attr = getattr(current_model, relation_name)
                if hasattr(relation_attr, "property") and hasattr(relation_attr.property, "mapper"):
                    target_model = relation_attr.property.mapper.class_
                    if target_model not in joined_models:
                        from sqlalchemy.orm import contains_eager
                        query = query.join(relation_attr)
                        eager_option = contains_eager(relation_attr) if eager_option is None else eager_option.contains_eager(relation_attr)
                        query = query.options(eager_option)
                        joined_models.add(target_model)
                    else:
                        from sqlalchemy.orm import contains_eager
                        eager_option = contains_eager(relation_attr) if eager_option is None else eager_option.contains_eager(relation_attr)
                    current_model = target_model
                else:
                    current_model = relation_attr
            else:
                return query

        if hasattr(current_model, field_name) or (current_model == self.model and field_name in query.selected_columns):
            column = getattr(current_model, field_name, None) or query.selected_columns[field_name]
            return query.where(self._OPERATORS[operator](column, value))
        return query

    def _apply_sorting(self, query: Any, order_by: str) -> Any:
        from sqlalchemy import desc, asc
        if order_by.startswith("-"):
            field_name = order_by[1:]
            direction = desc
        else:
            field_name = order_by
            direction = asc

        if hasattr(self.model, field_name) or field_name in query.selected_columns:
            column = getattr(self.model, field_name, None) or query.selected_columns[field_name]
            return query.order_by(direction(column))
        raise ValueError(f"Invalid sort field '{field_name}' for model {self.model.__name__}")
