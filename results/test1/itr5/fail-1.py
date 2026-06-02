import sys

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

# read input from stdin
input_list = [int(x.strip()) for x in sys.stdin]

# compute sum and mean
sum = 0
for num in input_list:
    sum += num
mean = sum / len(input_list)

# print results
print("Sum:", sum)
print("Average:", round(mean, 2))

# test functions
assert add(2, 3) == 5
assert add(-1, 1) == 0
assert add(0, 0) == 0

assert subtract(10, 4) == 6
assert subtract(0, 5) == -5

assert multiply(3, 4) == 12
assert multiply(-2, 5) == -10
assert multiply(0, 999) == 0