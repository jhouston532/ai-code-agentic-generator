import sys

# Get the number of items in the list
num = int(sys.stdin.readline())
print("Units:", num)

# Sum all the items in the list
sum_of_items = sum([float(i) for i in sys.stdin])
print("Sum:", round(sum_of_items, 2))

# Compute average of all items in the list
avg = round(sum_of_items / num, 2)
print("Average:", avg)
import sys


def main():
    # Get the number of items in the list
    num = int(sys.stdin.readline())

    # Sum all the items in the list
    sum_of_items = sum([float(i) for i in sys.stdin])

    print("Units:", num)
    print("Sum:", round(sum_of_items, 2))

    # Compute average of all items in the list
    avg = round(sum_of_items / num, 2)
    print("Average:", avg)


if __name__ == "__main__":
    main()