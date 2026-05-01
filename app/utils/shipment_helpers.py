import random
import string

def generate_vehicle_plate() -> str:
    """
    Generates a random vehicle plate following the AAA123 format.
    3 Uppercase letters followed by 3 digits.
    """
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"{letters}{numbers}"


def generate_fleet_number() -> str:
    """
    Generates a random fleet number following the AAA1234A format.
    3 Uppercase letters, 4 digits, and 1 final Uppercase letter.
    """
    letters_prefix = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=4))
    letter_suffix = random.choice(string.ascii_uppercase)
    return f"{letters_prefix}{numbers}{letter_suffix}"
