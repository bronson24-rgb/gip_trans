def test_summary_computes_profit_correctly(client, auth_headers, valid_route_report_payload):
    headers, _user = auth_headers

    report = client.post("/api/route-reports", json=valid_route_report_payload, headers=headers).json()
    client.patch(f"/api/route-reports/{report['id']}", json={"revenue_amount": "25000.00"}, headers=headers)
    client.post(
        f"/api/route-reports",
        json={
            **valid_route_report_payload,
            "vehicle_id": report["vehicle_id"],
            "fuel_refills": [
                {
                    "refill_datetime": "2026-07-24T08:00:00Z",
                    "station_name": "АЗС",
                    "liters": "60",
                    "total_cost": "6000.00",
                }
            ],
        },
        headers=headers,
    )
    client.post(
        "/api/expenses",
        json={"expense_date": "2026-07-24", "category": "rent", "amount": "5000.00"},
        headers=headers,
    )

    response = client.get(
        "/api/summary", params={"date_from": "2026-07-01", "date_to": "2026-07-31"}, headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["revenue"] == "25000.00"
    assert body["fuel_cost"] == "6000.00"
    assert body["other_expenses"] == "5000.00"
    assert body["profit"] == "14000.00"


def test_summary_outside_date_range_is_excluded(client, auth_headers, valid_route_report_payload):
    headers, _user = auth_headers
    valid_route_report_payload["report_date"] = "2026-01-01"
    report = client.post("/api/route-reports", json=valid_route_report_payload, headers=headers).json()
    client.patch(f"/api/route-reports/{report['id']}", json={"revenue_amount": "1000.00"}, headers=headers)

    response = client.get(
        "/api/summary", params={"date_from": "2026-07-01", "date_to": "2026-07-31"}, headers=headers
    )

    body = response.json()
    assert body["revenue"] == "0"
    assert body["profit"] == "0"


def test_summary_with_no_data_returns_zeroes(client, auth_headers):
    headers, _user = auth_headers

    response = client.get(
        "/api/summary", params={"date_from": "2026-01-01", "date_to": "2026-01-31"}, headers=headers
    )

    body = response.json()
    assert body["revenue"] == "0"
    assert body["fuel_cost"] == "0"
    assert body["other_expenses"] == "0"
    assert body["profit"] == "0"
