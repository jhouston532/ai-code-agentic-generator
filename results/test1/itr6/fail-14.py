Here is a complete and immediately runnable Python script that meets the requirements:
```python
import sys

# Initialize variables for sum, mean, and input list
sum = 0
mean = None
input_list = []

# Loop over each integer received on standard input stream
for line in sys.stdin:
    # Try to convert the current line to an integer
    try:
        num = int(line)
    except ValueError:
        continue

    # Add current number to sum and append it to input list
    sum += num
    input_list.append(num)

# Compute mean by dividing sum by length of input list (only if there are valid numbers)
if len(input_list) > 0:
    mean = round(sum / len(input_list), 2)

# Print both values in the format shown in EXPECTED_OUTPUT
print("Sum:", sum)
if mean is not None:
    print("Average:", mean)
```
This script handles invalid input by using exception handling and only computes the mean when there are valid numbers available. It also simplifies the code by removing unnecessary functions like `add`, `subtract`, and `multiply`.