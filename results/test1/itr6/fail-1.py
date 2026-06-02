import sys

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

# read input from stdin
input_list = []
for line in sys.stdin:
    input_list.append(int(line))

# compute sum and mean
sum = 0
mean = 0
for num in input_list:
    sum += num
    mean += (num / len(input_list))

# print results
print("Sum:", sum)
print("Average:", round(mean, 2))

# EXPECTED OUTPUT
# Sum: 150
# Average: 30.00