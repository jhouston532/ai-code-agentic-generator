import sys

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

# read input from stdin
input_list = [int(x) for x in sys.stdin]

# compute sum and mean
sum = 0
for num in input_list:
    sum += num
mean = sum / len(input_list)

# print results
print("Sum:", sum)
print("Average:", round(mean, 2))
```
This script will read a list of integers from stdin (one per line), compute their sum and mean, then print both values in the format shown in EXPECTED_OUTPUT.

To test this script, you can run it with the following command:
```
python task_with_tests.py <<INPUT
10
20
30
40
50
```
This will read the input from stdin and print the results to stdout. The output should match EXPECTED_OUTPUT exactly, including the whitespace at the beginning of each line.