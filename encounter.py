import random

def dice_roll():
    result = random.randint(1, 20)
    print(f"Rolling dice! You got {result}.")
    return result