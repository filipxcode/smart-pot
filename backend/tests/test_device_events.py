import uuid

import pytest


pytestmark = pytest.mark.asyncio


async def test_create_event_requires_auth(client, device):
    r = await client.post(
        "/device-events",
        json={"device_id": device["id"], "event_type": "watering"},
    )
    assert r.status_code == 401


async def test_create_event(client, device, auth_headers):
    r = await client.post(
        "/device-events",
        json={"device_id": device["id"], "event_type": "watering", "note": "200ml"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["device_id"] == device["id"]
    assert body["event_type"] == "watering"
    assert body["note"] == "200ml"
    assert "id" in body and "created_at" in body


async def test_cannot_create_event_for_foreign_device(client, device, other_auth_headers):
    r = await client.post(
        "/device-events",
        json={"device_id": device["id"], "event_type": "pruning"},
        headers=other_auth_headers,
    )
    assert r.status_code != 201


async def test_list_events_filtered_by_owner_and_device(
    client, device, auth_headers, other_auth_headers
):
    await client.post(
        "/device-events",
        json={"device_id": device["id"], "event_type": "watering"},
        headers=auth_headers,
    )
    other_device = (
        await client.post(
            "/devices",
            json={"name": "x", "serial": "OTHER"},
            headers=other_auth_headers,
        )
    ).json()
    await client.post(
        "/device-events",
        json={"device_id": other_device["id"], "event_type": "watering"},
        headers=other_auth_headers,
    )

    r = await client.get("/device-events", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["device_id"] == device["id"]

    r = await client.get(f"/device-events?device_id={device['id']}", headers=auth_headers)
    assert all(e["device_id"] == device["id"] for e in r.json())


async def test_get_update_delete_event(client, device, auth_headers):
    created = (
        await client.post(
            "/device-events",
            json={"device_id": device["id"], "event_type": "fertilization", "note": "n1"},
            headers=auth_headers,
        )
    ).json()
    eid = created["id"]

    r = await client.get(f"/device-events/{eid}", headers=auth_headers)
    assert r.status_code == 200

    r = await client.patch(
        f"/device-events/{eid}", json={"note": "updated"}, headers=auth_headers
    )
    assert r.status_code == 200
    assert r.json()["note"] == "updated"

    r = await client.delete(f"/device-events/{eid}", headers=auth_headers)
    assert r.status_code == 204

    r = await client.get(f"/device-events/{eid}", headers=auth_headers)
    assert r.status_code == 404


async def test_get_event_404_for_other_user(client, device, auth_headers, other_auth_headers):
    created = (
        await client.post(
            "/device-events",
            json={"device_id": device["id"], "event_type": "watering"},
            headers=auth_headers,
        )
    ).json()
    r = await client.get(f"/device-events/{created['id']}", headers=other_auth_headers)
    assert r.status_code == 404


async def test_get_unknown_event_404(client, auth_headers):
    r = await client.get(f"/device-events/{uuid.uuid4()}", headers=auth_headers)
    assert r.status_code == 404


async def test_invalid_event_type_rejected(client, device, auth_headers):
    r = await client.post(
        "/device-events",
        json={"device_id": device["id"], "event_type": "not-a-real-event"},
        headers=auth_headers,
    )
    assert r.status_code == 422
