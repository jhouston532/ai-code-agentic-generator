import sys

def main():
    # Check if there are any arguments provided
    if len(sys.argv) < 2:
        print("Usage: python script.py numbers...", file=sys.stderr)
        return

    try:
        # Read the list of numerical values from command-line argument(s)
        values = [float(arg) for arg in sys.argv[1:]]

        # Check if all values are numeric and not empty
        if not all(isinstance(value, (int, float)) for value in values):
            raise ValueError("All provided values must be numeric.")

        num_of_values = len(values)
        total_sum = sum(values)
        average = total_sum / num_of_values

        # Print the results with f-strings for better readability
        print(f"Units: {num_of_values}")
        print(f"Sum: {total_sum}")
        print(f"Average: {average}")
    except ValueError as e:
        # Handle non-numeric inputs gracefully
        print(f"Error: {e}. Please provide only numeric values.", file=sys.stderr)

if __name__ == "__main__":
    main()