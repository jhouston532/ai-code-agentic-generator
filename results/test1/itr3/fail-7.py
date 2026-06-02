# Calculate sum and mean of list of integers from stdin
import sys

def calculate_stats(numbers):
    """Calculate sum and mean of a list of integers"""
    sum = 0
    for number in numbers:
        sum += int(number)
    mean = sum / len(numbers)
    return (sum, round(mean, 2))

if __name__ == "__main__":
    # Get input from stdin
    numbers = sys.stdin.read().splitlines()

    # Calculate sum and mean
    (sum, mean) = calculate_stats(numbers)

    # Print results
    print("Sum:", sum)
    print("Average:", round(mean, 2))
```
This script will read a list of integers from stdin, calculate their sum and mean, and print the results in the format specified in the task.

To run this script, save it to a file with a `.py` extension (e.g., `script.py`) and then run it using the Python interpreter:
```
python script.py
```
The input should be provided on stdin, one integer per line. The output will be printed to stdout.

For example, if the input is:
```
10
20
30
40
50
```
The output will be:
```
Sum: 150
Average: 30.00