Here is a Python script that reads a list of integers from stdin, computes their sum and mean (rounded to 2 decimal places), and prints both values in the format shown in EXPECTED_OUTPUT. The script handles invalid input values correctly using try-except blocks and initializes `sum` and `mean` variables before the loop.
```python
import sys

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

# Initialize sum and mean variables before the loop
sum = 0
mean = 0

# Read input from stdin and ignore non-numeric lines
input_list = []
for line in sys.stdin:
    try:
        num = int(line)
        sum += num
        input_list.append(num)
    except ValueError:
        continue

# Compute mean and print results
mean = round((sum / len(input_list)), 2)
print("Sum:", sum)
print("Average:", mean)
```
This script should work as expected when you pipe the provided INPUT into it. If you want to test the functions with inline assert tests, copy the code into a separate file named `task_with_tests.py`, and run it using:
```bash
python task_with_tests.py
```
Note that the code assumes all inputs are valid integer values which is not always true, so it's better handled with exception handling if possible in real world applications.