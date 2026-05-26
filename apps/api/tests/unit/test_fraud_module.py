from types import SimpleNamespace

from app.modules.fraud import FraudModule


def test_score_order_coerces_string_numeric_fields():
    module = FraudModule.__new__(FraudModule)
    order = SimpleNamespace(
        billing_country="CA",
        shipping_country="US",
        billing_postal_code="A1A1A1",
        shipping_postal_code="B2B2B2",
        total="300.50",
        payment_attempt_count="3",
    )
    customer = SimpleNamespace(total_orders="1")

    score, status, reasons = FraudModule._score_order(module, order, customer)

    assert score == 110
    assert status == "high_risk"
    assert "billing_shipping_country_mismatch" in reasons
    assert "billing_shipping_postal_mismatch" in reasons
    assert "high_value_first_order" in reasons
    assert "elevated_payment_attempt_count" in reasons
    assert "low_history_high_total" in reasons
