"""Deterministic order helpers for TestFlow business-logic demos."""


def calculate_discount(total, customer_type):
    """Return the discount amount for a customer type and order total."""
    if total < 0:
        raise ValueError("total cannot be negative")

    discount_rates = {
        "regular": 0.0,
        "vip": 0.15,
        "student": 0.10,
    }

    if customer_type not in discount_rates:
        raise ValueError("unknown customer type")

    return total * discount_rates[customer_type]


def validate_order(items):
    """Return True when all order items satisfy required business rules."""
    if not isinstance(items, list):
        raise ValueError("items must be a list")
    if not items:
        raise ValueError("items cannot be empty")

    required_fields = {"name", "quantity", "price"}

    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each item must be a dictionary")
        if not required_fields.issubset(item):
            raise ValueError("each item must include name, quantity, and price")
        if item["quantity"] <= 0:
            raise ValueError("quantity must be greater than zero")
        if item["price"] < 0:
            raise ValueError("price cannot be negative")

    return True


def compute_shipping(weight, region):
    """Return shipping cost for a package weight and destination region."""
    if weight <= 0:
        raise ValueError("weight must be greater than zero")

    shipping_rules = {
        "local": (5, 1),
        "domestic": (10, 2),
        "international": (25, 5),
    }

    if region not in shipping_rules:
        raise ValueError("unknown region")

    base_cost, per_weight_cost = shipping_rules[region]
    return base_cost + weight * per_weight_cost
