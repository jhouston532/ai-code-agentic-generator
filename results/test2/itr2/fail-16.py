import sys

# Check if there are enough arguments provided by the user
if len(sys.argv) < 2:
    print("No input provided.")
    sys.exit()

# Extract numerical values from command line arguments
values = []
for arg in sys.argv[1:]:
    try:
        value = float(arg)
        values.append(value)
    except ValueError as e:
        print(f"Invalid input: {arg} is not a number. Error: {e}")

# Calculate the required statistics
units = len(values)
if units == 0:
    average = 0
else:
    total_sum = sum(values)
    average = total_sum / units

# Print the results
print("Units:", units)
print("Sum:", total_sum if units > 0 else "N/A")
print("Average:", average)