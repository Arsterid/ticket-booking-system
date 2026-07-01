from src.core.infra.transport.http import GenericRequestSchema


class RegisterViewsRequestSchema(GenericRequestSchema):
    model_name: str
    object_ids: list[int]
