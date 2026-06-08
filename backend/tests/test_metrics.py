from datetime import datetime, timedelta, timezone

import pytest

from api.models.metric import Metric


pytestmark = pytest.mark.asyncio


async def test_create_metric_requires_auth(client, device):
    r = await client.post("/metrics", json={"device_id": device["id"], "air_temp": 21.5})
    assert r.status_code == 401


async def test_create_metric(client, device, auth_headers):
    r = await client.post(
        "/metrics",
        json={
            "device_id": device["id"],
            "air_temp": 22.5,
            "air_hum": 55.0,
            "soil_hum": 40,
        },
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["device_id"] == device["id"]
    assert body["air_temp"] == 22.5
    assert body["soil_hum"] == 40
    assert body["root_temp"] is None
    assert "created_at" in body


async def test_cannot_post_metric_for_foreign_device(client, device, other_auth_headers):
    r = await client.post(
        "/metrics",
        json={"device_id": device["id"], "air_temp": 1.0},
        headers=other_auth_headers,
    )
    assert r.status_code != 201


async def test_webhook_ingests_without_auth(client, device, auth_headers):
    r = await client.post(
        "/metrics/webhook",
        json={"device_id": device["id"], "air_temp": 23.4, "soil_hum": 38},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["device_id"] == device["id"]
    assert body["air_temp"] == 23.4
    assert body["soil_hum"] == 38

    latest = await client.get(f"/metrics/{device['id']}/latest", headers=auth_headers)
    assert latest.status_code == 200
    assert latest.json()["air_temp"] == 23.4


async def test_webhook_unknown_device(client):
    r = await client.post(
        "/metrics/webhook",
        json={"device_id": 999999, "air_temp": 1.0},
    )
    assert r.status_code == 404


async def test_latest_metric_empty(client, device, auth_headers):
    r = await client.get(f"/metrics/{device['id']}/latest", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() is None


async def test_latest_returns_newest(session_maker, client, device, auth_headers):
    base = datetime.now(timezone.utc) - timedelta(hours=1)
    async with session_maker() as s:
        s.add_all([
            Metric(device_id=device["id"], air_temp=10.0, created_at=base),
            Metric(device_id=device["id"], air_temp=15.0, created_at=base + timedelta(minutes=10)),
            Metric(device_id=device["id"], air_temp=25.0, created_at=base + timedelta(minutes=20)),
        ])
        await s.commit()

    r = await client.get(f"/metrics/{device['id']}/latest", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["air_temp"] == 25.0


async def test_history_returns_inserted(session_maker, client, device, auth_headers):
    base = datetime.now(timezone.utc) - timedelta(hours=1)
    async with session_maker() as s:
        s.add_all([
            Metric(device_id=device["id"], air_temp=1.0, created_at=base),
            Metric(device_id=device["id"], air_temp=2.0, created_at=base + timedelta(minutes=1)),
            Metric(device_id=device["id"], air_temp=3.0, created_at=base + timedelta(minutes=2)),
        ])
        await s.commit()

    r = await client.get(f"/metrics/{device['id']}/history", headers=auth_headers)
    assert r.status_code == 200
    temps = [m["air_temp"] for m in r.json()]
    assert temps == [1.0, 2.0, 3.0]


async def test_history_days_validation(client, device, auth_headers):
    r = await client.get(
        f"/metrics/{device['id']}/history?days=0", headers=auth_headers
    )
    assert r.status_code == 422
    r = await client.get(
        f"/metrics/{device['id']}/history?days=999", headers=auth_headers
    )
    assert r.status_code == 422


async def test_history_for_foreign_device_does_not_leak(
    client, device, auth_headers, other_auth_headers
):
    await client.post(
        "/metrics",
        json={"device_id": device["id"], "air_temp": 99.9},
        headers=auth_headers,
    )
    r = await client.get(f"/metrics/{device['id']}/history", headers=other_auth_headers)
    if r.status_code == 200:
        assert r.json() == []
    else:
        assert r.status_code in (403, 404)
