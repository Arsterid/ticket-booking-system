import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_create_category_success(admin_client):
    payload = {"name": "New Category"}
    response = await admin_client.post("/admin/categories", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "New Category"


@pytest.mark.asyncio
async def test_admin_get_categories_success(admin_client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "event_category", id=1, name="Music")
        

    response = await admin_client.get("/admin/categories?limit=10&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "Music"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"name": ""},
        {"name": "   "},
        {"name": "A" * 300},
        {"name": "Valid", "extra_field": "forbidden"},
        {},
    ],
)
async def test_create_category_validation_errors(admin_client, payload):
    response = await admin_client.post("/admin/categories", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_create_category_non_existent_parent(admin_client):
    payload = {"name": "Sub Category", "parent_id": 9999}
    response = await admin_client.post("/admin/categories", json=payload)
    assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST]


@pytest.mark.asyncio
async def test_create_sub_category_success(admin_client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "event_category", id=100, name="Parent Category")
        

    payload = {"name": "Sub Category", "parent_id": 100}
    response = await admin_client.post("/admin/categories", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "Sub Category"


@pytest.mark.asyncio
async def test_create_category_duplicate(admin_client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "event_category", id=200, name="Unique Name")
        

    payload = {"name": "Unique Name"}
    response = await admin_client.post("/admin/categories", json=payload)
    assert response.status_code in [status.HTTP_409_CONFLICT, status.HTTP_400_BAD_REQUEST]


@pytest.mark.asyncio
@pytest.mark.parametrize("search_query", ["music", "MUSIC", "MuSiC"])
async def test_admin_get_categories_case_insensitive(admin_client, setup_uow, create_model_factory, search_query):
    async with setup_uow as uow:
        await create_model_factory(uow, "event_category", id=300, name="Music")
        

    response = await admin_client.get(f"/admin/categories?limit=10&offset=0&name={search_query}")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
