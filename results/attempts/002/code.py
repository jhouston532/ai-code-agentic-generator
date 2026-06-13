import sys

# Read the list of numerical values from command line arguments
values = [float(arg) for arg in sys.argv[1:]]

# Calculate the number of items, sum, and average
units = len(values)
total_sum = sum(values)

if units == 0:
    print("Units: 0")
    print("Sum: 0")
    print("Average: 0.0")
else:
    average = total_sum / units
    print(f"Units: {units}")
    print(f"Sum: {total_sum}")
    print(f"Average: {average:.1f}")