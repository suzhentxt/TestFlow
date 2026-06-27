"""Deterministic calculator helpers for TestFlow demonstrations."""


def add(a, b):
    """Return the sum of two numbers."""
    return a + b


def subtract(a, b):
    """Return the difference between two numbers."""
    return a - b


def divide(a, b):
    """Return a divided by b, raising ValueError for division by zero."""
    if b == 0:
        raise ValueError("cannot divide by zero")
    return a / b


def factorial(n):
    """Return n factorial for a non-negative integer."""
    if n < 0:
        raise ValueError("n cannot be negative")
    if n in (0, 1):
        return 1

    result = 1
    for value in range(2, n + 1):
        result *= value
    return result


def is_prime(n):
    """Return True if n is prime, otherwise False."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor += 2

    return True
