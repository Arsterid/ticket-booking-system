from typing import Any, Set, Type, Tuple, List

from sqlalchemy import select, tuple_
from sqlalchemy.orm import contains_eager

from .resolver import FilterResolver


class QueryFilterApplier:
    @classmethod
    def _prepare_filters(
            cls: Type["QueryFilterApplier"],
            model: Type[Any],
            filters: dict[str, Any],
            operators_map: dict[str, Any]
    ) -> List[Tuple[Any, Any, List[Any]]]:
        prepared = []
        for key, v in filters.items():
            if v is None:
                continue

            val = v.resolve(model, operators_map) if hasattr(v, "resolve") else v
            res = FilterResolver.resolve(model, key, operators_map)
            if res.column is None:
                continue

            prepared.append((val, res, list(res.relations)))
        return prepared

    @classmethod
    def apply_context_filters(
            cls: Type["QueryFilterApplier"],
            stmt: Any,
            model: Type[Any],
            filters: dict[str, Any],
            operators_map: dict[str, Any]
    ) -> Any:
        joined_models: Set[Type[Any]] = set()
        eager_options: dict[Tuple[Any, ...], Any] = {}

        prepared_filters = cls._prepare_filters(model, filters, operators_map)

        for val, res, relations in prepared_filters:
            current_eager_chain = None
            relations_path = []
            is_new_path = False

            for rel_attr in relations:
                prop = rel_attr.property
                next_model = prop.mapper.class_
                relations_path.append(rel_attr)

                if next_model not in joined_models:
                    stmt = stmt.join(rel_attr)
                    joined_models.add(next_model)
                    is_new_path = True

                if is_new_path:
                    if current_eager_chain is None:
                        current_eager_chain = contains_eager(rel_attr)
                    else:
                        current_eager_chain = current_eager_chain.contains_eager(rel_attr)

            if is_new_path and current_eager_chain is not None:
                eager_options[tuple(relations_path)] = current_eager_chain

            stmt = stmt.where(operators_map[res.operator](res.column, val))

        if eager_options:
            stmt = stmt.options(*eager_options.values())

        return stmt

    @classmethod
    def apply_modification_filters(
            cls: Type["QueryFilterApplier"],
            stmt: Any,
            model: Type[Any],
            filters: dict[str, Any],
            operators_map: dict[str, Any]
    ) -> Any:
        prepared_filters = cls._prepare_filters(model, filters, operators_map)

        for val, res, relations in prepared_filters:
            if not relations:
                stmt = stmt.where(operators_map[res.operator](res.column, val))
                continue

            first_rel = relations[0]
            prop = first_rel.property

            local_fks = list(prop.local_columns)
            remote_pks = list(prop.remote_side)

            subq = select(*[getattr(prop.mapper.class_, pk.name) for pk in remote_pks])

            for rel_attr in relations[1:]:
                subq = subq.join(rel_attr)

            subq = subq.where(operators_map[res.operator](res.column, val))

            if len(local_fks) > 1:
                stmt = stmt.where(tuple_(*local_fks).in_(subq.scalar_subquery()))
            else:
                stmt = stmt.where(local_fks[0].in_(subq.scalar_subquery()))

        return stmt
