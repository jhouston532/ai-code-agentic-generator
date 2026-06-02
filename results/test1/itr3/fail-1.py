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
This script reads a list of integers from stdin (one per line), computes their sum and mean (rounded to 2 decimal places), then prints both values in the format shown in EXPECTED_OUTPUT.

To run this script, save it to a file with a `.py` extension (e.g., `script.py`) and then run it with the command `python script.py`. The input data can be piped into the script using a redirect, like this: `echo -e "10\n20\n30\n40\n50" | python script.py`.

Note that this script uses the `sys` module to read from stdin and the `round()` function to round the mean value to 2 decimal places.