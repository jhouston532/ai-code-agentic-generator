import sys

def main():
    # Check if there are any arguments provided
    if len(sys.argv) < 2:
        print("Usage: python script.py numbers...", file=sys.stderr)
        return

    try:
        # Read the list of numerical values from command-line argument(s)
        values = [float(arg) for arg in sys.argv[1:]]
        
        # Calculate the number of items, sum, and average
        units = len(values)
        total_sum = sum(values)
        average = total_sum / units

        # Print the results
        print("Units:", units)
        print("Sum:", total_sum)
        print("Average:", average)
    except ValueError as e:
        # Handle non-numeric inputs gracefully
        print(f"Error: {e}. Please provide only numeric values.", file=sys.stderr)

if __name__ == "__main__":
    main()