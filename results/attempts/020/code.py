import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 script.py numbers...", file=sys.stderr)
        return

    try:
        values = [float(arg) for arg in sys.argv[1:]]
        
        if not values:
            raise ValueError("No Numerical values provided")
    
    except ValueError as e:
        print(f"Invalid Input. Please provide only numeric inputs.\n{e}", file=sys.stderr)
        return

    num_units = len(values)
    total_sum = sum(values)
    average = total_sum / num_units

    print(f"Units: {num_units}")
    print(f"Sum: {total_sum}")
    print(f"Average: {average:.2f}")

if __name__ == "__main__":
    main()