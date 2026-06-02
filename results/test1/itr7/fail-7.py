import sys

def safe_input():
    try:
        return int(sys.stdin.readline().strip())
    except ValueError:
        print("Invalid input! Please enter an integer.")
        return None

sum_of_numbers = 0
count = 0

while True:
    num = safe_input()
    if num is None:
        continue
    sum_of_numbers += num
    count += 1
    if count == len(sys.argv) - 1:  # Check if all numbers have been read (if provided as command line arguments)
        break

average = round(sum_of_numbers / count, 2)
print(f"Sum: {sum_of_numbers}")
print(f"Average: {average}")