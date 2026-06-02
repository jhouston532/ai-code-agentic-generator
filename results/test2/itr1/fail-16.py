import sys

def main():
    if len(sys.argv) < 2:
        print("No input provided.", file=sys.stderr)
        return

    numbers = []
    try:
        for arg in sys.argv[1:]:
            number = float(arg)
            numbers.append(number)
    except ValueError as e:
        print(f"Error: {e} - Please enter numeric values only.", file=sys.stderr)
        return

    units = len(numbers)
    total_sum = sum(numbers)
    average = total_sum / units if units > 0 else float('nan')

    print("Units:", units)
    print("Sum:", total_sum)
    print("Average:", average)

if __name__ == "__main__":
    main()