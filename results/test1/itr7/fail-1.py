import statistics

# Read the list of integers from stdin
numbers = []
for line in sys.stdin:
    numbers.append(int(line))

# Compute the sum and mean of the list
sum_of_numbers = sum(numbers)
mean = round(statistics.mean(numbers), 2)

# Print the results in the desired format
print("Sum:", sum_of_numbers)
print("Average:", mean)