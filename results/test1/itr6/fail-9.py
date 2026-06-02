Here's a corrected version of the script that fixes the indentation error and improves readability:

```python
import sys

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

sum = 0
mean = None
input_list = []
for line in sys.stdin:
    try:
        num = int(line)
        sum += num
        input_list.append(num)
    except ValueError:
        continue

if len(input_list) > 0:
    mean = round((sum / len(input_list)), 2)

print("Sum:", sum)
if mean is not None:
    print("Average:", mean)
```

This script should work as expected when you pipe the provided INPUT into it. If you want to test the functions with inline assert tests, copy the code into a separate file named `task_with_tests.py`, and run it using:

```bash
python task_with_tests.py
```

Note that the code assumes all inputs are valid integer values which is not always true, so it's better handled with exception handling if possible in real-world applications. Also, I added some checks to ensure that the mean calculation is only performed when there are valid input numbers available.