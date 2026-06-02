import sys

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

# Read the input from stdin
input_list = [int(line.strip()) for line in sys.stdin]

# Compute the sum and mean of the list
sum = sum(input_list)
mean = round(sum / len(input_list), 2)

# Print the results
print("Sum:", sum)
print("Average:", mean)

# Test the functions
assert add(2, 3) == 5
assert add(-1, 1) == 0
assert add(0, 0) == 0

assert subtract(10, 4) == 6
assert subtract(0, 5) == -5

assert multiply(3, 4) == 12
assert multiply(-2, 5) == -10
assert multiply(0, 999) == 0

# Print a message to indicate that the tests passed
print("All tests passed!")