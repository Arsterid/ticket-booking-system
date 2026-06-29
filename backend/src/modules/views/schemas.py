from src.core.infra.transport.http.schemas.base import GenericRequestSchema


class RegisterViewsRequestSchema(GenericRequestSchema):
    model_name: str
    object_ids: list[int]
