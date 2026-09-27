export const EXAMPLE_CODE = `def calculate_discount(price, age):
    if age < 18:
        return price * 0.5
    return price`

export const EXAMPLE_TESTS = `def test_adult():
    assert calculate_discount(100, 20) == 100`
