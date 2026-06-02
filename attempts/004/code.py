import sys

def main():
    # Read the list of numerical values from command line arguments
    values = [float(arg) for arg in sys.argv[1:] if arg.isdigit()]

    # Check if there are any values provided
    if not values:
        print("Usage: python script.py numbers...")
        return

    # Calculate the number of items, sum, and average
    units = len(values)
    total_sum = sum(values)
    average = total_sum / units

    # Print the results
    print("Units:", units)
    print("Sum:", total_sum)
    print("Average:", average)

if __name__ == "__main__":
    main()