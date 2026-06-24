from src.common.schemas import GenericRequestSchema


class BulkViewsSchema(GenericRequestSchema):
    model_name: str
    object_ids: list[int]
