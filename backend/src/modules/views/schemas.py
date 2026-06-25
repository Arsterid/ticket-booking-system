from src.core.infra.transport.http.schemas.base import GenericRequestSchema


class BulkViewsSchema(GenericRequestSchema):
    model_name: str
    object_ids: list[int]
