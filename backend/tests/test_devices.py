import pytest


pytestmark = pytest.mark.asyncio


async def test_create_device_requires_auth(client):
    r = await client.post("/devices", json={"name": "x", "serial": "s1"})
    assert r.status_code == 401


async def test_create_device(client, auth_headers):
    r = await client.post(
        "/devices",
        json={"name": "Basil", "serial": "SN-AAA"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Basil"
    assert body["serial"] == "SN-AAA"
    assert body["id"] > 0
    assert "owner_id" in body


async def test_list_returns_only_owned_devices(client, auth_headers, other_auth_headers):
    await client.post("/devices", json={"name": "mine", "serial": "S-1"}, headers=auth_headers)
    await client.post("/devices", json={"name": "theirs", "serial": "S-2"}, headers=other_auth_headers)

    r = await client.get("/devices", headers=auth_headers)
    assert r.status_code == 200
    serials = [d["serial"] for d in r.json()]
    assert serials == ["S-1"]


async def test_get_device_404_for_other_user(client, device, other_auth_headers):
    r = await client.get(f"/devices/{device['id']}", headers=other_auth_headers)
    assert r.status_code == 404


async def test_update_device(client, device, auth_headers):
    r = await client.patch(
        f"/devices/{device['id']}",
        json={"name": "Renamed"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed"
    assert r.json()["serial"] == device["serial"]  


async def test_delete_device(client, device, auth_headers):
    r = await client.delete(f"/devices/{device['id']}", headers=auth_headers)
    assert r.status_code == 204

    r = await client.get(f"/devices/{device['id']}", headers=auth_headers)
    assert r.status_code == 404


async def test_duplicate_serial_rejected(client, auth_headers):
    await client.post("/devices", json={"name": "a", "serial": "DUP"}, headers=auth_headers)
    r = await client.post("/devices", json={"name": "b", "serial": "DUP"}, headers=auth_headers)
    assert r.status_code == 409
