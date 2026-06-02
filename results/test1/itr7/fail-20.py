import statistics
import sys

def main():
    total = 0
    count = 0
    for line in sys.stdin:
        try:
            num = int(line)
            total += num
            count += 1
        except ValueError:
            print("Invalid Input! Please enter an integer.")
    if count == 0:
        print("No valid number was inputted")
    else:
        average = round(statistics.mean(total), 2)
        print(f"Sum : {total}")
        print(f"Average: {average}")

if __name__ == "__main__":
    main()