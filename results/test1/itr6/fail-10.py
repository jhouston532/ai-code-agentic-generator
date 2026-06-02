# Write a Python script that reads a list of integers from stdin (one per line), computes their sum and mean (rounded to 2 decimal places), then prints both values in the format shown in EXPECTED_OUTPUT.

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
        # If conversion fails, skip to next iteration of loop
        continue
    
    # Add current number to sum and append it to input list
    sum += num
    input_list.append(num)

# Compute mean by dividing sum by length of input list
mean = round(sum / len(input_list), 2)

# Print both values in the format shown in EXPECTED_OUTPUT
print("Sum:", sum)
print("Average:", mean)

# Note that this script assumes all inputs are valid integer values, which may not always be true. It's better to handle invalid input with exception handling if possible in real-world applications.