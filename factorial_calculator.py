def factorial(n): 
    if n == 0 or n == 1: 
        return 1 
    else:
        return n * factorial(n-1) 

def get_factorial_input():
    """Prompt the user for a non-negative integer and return its factorial."""
    while True:
        try:
            user_input = int(input("Enter a non-negative integer to calculate its factorial: "))
            if user_input < 0:
                print("Please enter a non-negative integer.")
                continue
            return user_input
        except ValueError:
            print("Invalid input. Please enter a valid non-negative integer.")

def test_factorial():
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(2) == 2
    assert factorial(3) == 6
    assert factorial(4) == 24
    assert factorial(5) == 120
    try:
        factorial(-1)
    except ValueError as e:
        assert str(e) == "Factorial is not defined for negative numbers."

number = get_factorial_input()
print(f"The factorial of {number} is {factorial(number)}.")

