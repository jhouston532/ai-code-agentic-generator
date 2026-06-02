Here is a corrected version of your script that handles non-numeric input gracefully and computes the sum and mean correctly:

```python
import sys

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

# read inputs from stdin and validate each line
valid_inputs = []
for line in sys.stdin:
    try:
        num = int(line.strip())
        valid_inputs.append(num)
    except ValueError:
        print(f"Error: Invalid integer '{line.strip()}'")
        continue

if not valid_inputs:
    print("Sum: 0\nAverage : None")
    sys.exit(1)

sum = 0
for num in valid_inputs:
    sum += num
mean = round(sum / len(valid_inputs), 2)

print("Sum:", sum)
print("Average:", mean)
```

This script reads inputs from stdin, validates each line to ensure it contains a valid integer, and computes the sum and mean if there are valid inputs. If no valid inputs are found, it prints "Sum: 0\nAverage : None" and exits with a non-zero status code (1).

The script also includes error handling for invalid integers by using a try-except block around the input validation part of the code. In case an invalid integer is encountered, it prints a meaningful error message and continues to process the remaining inputs.