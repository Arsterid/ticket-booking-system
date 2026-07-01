from typing import Any

from sqlalchemy import select


class F:
    def __init__(self, path: str):
        self.path = path

    def resolve(self, current_model: Any) -> Any:
        parts = self.path.split("__")
        target_field = parts.pop()

        model = current_model
        stmt = None
        last_remote_col = None

        for relation_name in parts:
            if not hasattr(model, relation_name):
                raise AttributeError(f"Could not resolve relation '{relation_name}' in path: {self.path}")

            relation_attr = getattr(model, relation_name)
            prop = relation_attr.property
            target_model = prop.mapper.class_

            local_col = prop.local_columns.copy().pop()
            remote_col = prop.remote_side.copy().pop()

            if stmt is None:
                stmt = select(target_model).where(remote_col == local_col)
            else:
                stmt = stmt.join(target_model, remote_col == last_remote_col)

            last_remote_col = remote_col
            model = target_model

        if stmt is not None:
            stmt = stmt.with_only_columns(getattr(model, target_field))
            return stmt.scalar_subquery()

        raise AttributeError(f"Could not resolve F-expression path: {self.path}")
