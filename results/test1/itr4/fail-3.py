Here's a Python script that reads a list of integers from standard input (one per line), computes their sum and mean (rounded to 2 decimal places), and prints both values in the format shown in the expected output. The script also includes error handling for empty lines or non-integer values.

```python
import sys

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def main():
    input_list = []
    for line in sys.stdin:
        try:
            number = int(line.strip())
            input_list.append(number)
        except ValueError:
            print(f"Error: Invalid integer value '{line.strip()}'.")

    if not input_list:
        print("Error: No valid integers found in the input.")
        return

    sum = 0
    for number in input_list:
        sum += number

    mean = round(sum / len(input_list), 2)

    print("Sum:", sum)
    print("Average:", mean)

if __name__ == "__main__":
    main()
```

This script reads the input from standard input, validates each line as an integer, and appends it to a list if it is valid. If no valid integers are found, it prints an error message. After that, it computes the sum and mean of the valid integers and prints them in the expected format.

You can test this script by running it with the provided input:

```bash
echo -e "10\n20\n30\n40\n50" | python script.py