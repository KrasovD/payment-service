from fastapi.testclient import TestClient


def test_create_cash_payment(client: TestClient, order_1000):
    response = client.post(
        f"/orders/{order_1000.id}/payments",
        json={
            "amount": "300.00",
            "type": "cash",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["order_id"] == order_1000.id
    assert data["amount"] == "300.00"
    assert data["type"] == "cash"
    assert data["status"] == "pending"


def test_create_acquiring_payment(client: TestClient, order_1000):
    response = client.post(
        f"/orders/{order_1000.id}/payments",
        json={
            "amount": "300.00",
            "type": "acquiring",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["order_id"] == order_1000.id
    assert data["amount"] == "300.00"
    assert data["type"] == "acquiring"
    assert data["status"] == "pending"


def test_create_payment_returns_404_for_unknown_order(client: TestClient):
    response = client.post(
        "/orders/999999/payments",
        json={
            "amount": "300.00",
            "type": "cash",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Заказ не найден"


def test_create_payment_returns_422_for_invalid_body(client: TestClient, order_1000):
    response = client.post(
        f"/orders/{order_1000.id}/payments",
        json={
            "amount": "not-a-number",
            "type": "cash",
        },
    )

    assert response.status_code == 422


def test_create_payment_returns_422_for_invalid_type(client: TestClient, order_1000):
    response = client.post(
        f"/orders/{order_1000.id}/payments",
        json={
            "amount": "300.00",
            "type": "crypto",
        },
    )

    assert response.status_code == 422


def test_create_payment_returns_409_when_order_amount_would_be_exceeded(
    client: TestClient,
    order_1000,
):
    response_1 = client.post(
        f"/orders/{order_1000.id}/payments",
        json={
            "amount": "700.00",
            "type": "cash",
        },
    )
    assert response_1.status_code == 201

    response_2 = client.post(
        f"/orders/{order_1000.id}/payments",
        json={
            "amount": "400.00",
            "type": "acquiring",
        },
    )

    assert response_2.status_code == 409
    assert response_2.json()["detail"] == "Общая сумма платежей не может превышать сумму заказа"


def test_deposit_payment(client: TestClient, order_1000):
    create_response = client.post(
        f"/orders/{order_1000.id}/payments",
        json={
            "amount": "500.00",
            "type": "cash",
        },
    )
    payment_id = create_response.json()["id"]

    response = client.post(
        f"/payments/{payment_id}/deposit",
        json={"amount": "200.00"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == payment_id
    assert data["amount"] == "500.00"
    assert data["status"] == "succeeded"


def test_deposit_payment_returns_404_for_unknown_payment(client: TestClient):
    response = client.post(
        "/payments/999999/deposit",
        json={"amount": "200.00"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Платёж не найден"


def test_deposit_payment_returns_400_when_deposit_exceeds_payment_amount(
    client: TestClient,
    order_1000,
):
    create_response = client.post(
        f"/orders/{order_1000.id}/payments",
        json={
            "amount": "300.00",
            "type": "cash",
        },
    )
    payment_id = create_response.json()["id"]

    response = client.post(
        f"/payments/{payment_id}/deposit",
        json={"amount": "400.00"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Сумма внесения превышает сумму платежа"


def test_deposit_payment_returns_422_for_invalid_body(client: TestClient, order_1000):
    create_response = client.post(
        f"/orders/{order_1000.id}/payments",
        json={
            "amount": "300.00",
            "type": "cash",
        },
    )
    payment_id = create_response.json()["id"]

    response = client.post(
        f"/payments/{payment_id}/deposit",
        json={"amount": "abc"},
    )

    assert response.status_code == 422


def test_refund_payment(client: TestClient, order_1000):
    create_response = client.post(
        f"/orders/{order_1000.id}/payments",
        json={
            "amount": "500.00",
            "type": "cash",
        },
    )
    payment_id = create_response.json()["id"]

    deposit_response = client.post(
        f"/payments/{payment_id}/deposit",
        json={"amount": "400.00"},
    )
    assert deposit_response.status_code == 200

    response = client.post(
        f"/payments/{payment_id}/refund",
        json={"amount": "150.00"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == payment_id


def test_refund_payment_returns_404_for_unknown_payment(client: TestClient):
    response = client.post(
        "/payments/999999/refund",
        json={"amount": "100.00"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Платёж не найден"


def test_refund_payment_returns_400_when_refund_exceeds_deposited_amount(
    client: TestClient,
    order_1000,
):
    create_response = client.post(
        f"/orders/{order_1000.id}/payments",
        json={
            "amount": "500.00",
            "type": "cash",
        },
    )
    payment_id = create_response.json()["id"]

    deposit_response = client.post(
        f"/payments/{payment_id}/deposit",
        json={"amount": "200.00"},
    )
    assert deposit_response.status_code == 200

    response = client.post(
        f"/payments/{payment_id}/refund",
        json={"amount": "300.00"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Сумма возврата превышает внесённую сумму"


def test_refund_payment_returns_422_for_invalid_body(client: TestClient, order_1000):
    create_response = client.post(
        f"/orders/{order_1000.id}/payments",
        json={
            "amount": "500.00",
            "type": "cash",
        },
    )
    payment_id = create_response.json()["id"]

    response = client.post(
        f"/payments/{payment_id}/refund",
        json={"amount": None},
    )

    assert response.status_code == 422


def test_create_payment_rejects_non_positive_amount(client: TestClient, order_1000):
    response = client.post(
        f"/orders/{order_1000.id}/payments",
        json={"amount": "0", "type": "cash"},
    )

    assert response.status_code == 422


def test_deposit_rejects_non_positive_amount(client: TestClient, order_1000):
    create_response = client.post(
        f"/orders/{order_1000.id}/payments",
        json={"amount": "300.00", "type": "cash"},
    )
    payment_id = create_response.json()["id"]

    response = client.post(
        f"/payments/{payment_id}/deposit",
        json={"amount": "0"},
    )

    assert response.status_code == 422