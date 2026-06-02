import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py numbers...", file=sys.stderr)
        return

    try:
        values = [float(arg) for arg in sys.argv[1:]]
        units = len(values)
        total_sum = sum(values)
        average = total_sum / units

        print(f"Units: {units}")
        print(f"Sum: {total_sum}")
        print(f"Average: {average}")
    except ValueError as e:
        print(f"Error: {e}. Please provide only numeric values.", file=sys.stderr)

if __name__ == "__main__":
    main()