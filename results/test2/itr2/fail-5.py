import sys

def main():
     # Read the list of numbers from stdin
    numbers = list(map(float, sys.argv[1:]))

     # Calculate the number of units
    num_units = len(numbers)

     # Calculate the sum of all items in the list
    total_sum = sum(numbers)

     # Calculate the average of all items in the list
    if num_units > 0:
        avg = total_sum / num_units
    else:
        avg = 0

     # Print the results
    print("Units:", num_units)
    print("Sum:", round(total_sum, 2))
    print("Average:", round(avg, 2))

if __name__ == "__main__":
    main()