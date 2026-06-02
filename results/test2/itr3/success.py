import sys

# Read command-line arguments as numerical values
values = [float(arg) for arg in sys.argv[1:]]

# Calculate the count of units
units = len(values)

# Calculate the sum of the values
total_sum = int(sum(values)) if all(v.is_integer() for v in values) else sum(values)

# Calculate the average rounded to 1 decimal place
average = round(sum(values) / units, 1)

# Print the results
print("Units:", units)
print("Sum:", total_sum)
print("Average:", average)