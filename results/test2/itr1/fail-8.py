import sys

# Check if there are enough arguments provided by the user
if len(sys.argv) < 2:
    print("No input provided.")
    sys.exit()

# Extract numbers from command line arguments
numbers = []
for arg in sys.argv[1:]:
    try:
        number = float(arg)
        numbers.append(number)
    except ValueError:
        print(f"Invalid input: {arg}. Please provide numerical values only.")
        sys.exit()

# Calculate units (number of items), sum, and average
units = len(numbers)
total_sum = sum(numbers)
average = total_sum / units if units > 0 else 0

# Print the results
print(f"Units: {units}")
print(f"Sum: {total_sum:.2f}")
print(f"Average: {average:.2f}")