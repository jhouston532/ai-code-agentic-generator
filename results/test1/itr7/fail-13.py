import sys
from statistics import mean

sum_of_numbers = 0
count = 0

while True:
    line = sys.stdin.readline().strip()
    if not line:
        break

    try:
        num = int(line)
        sum_of_numbers += num
        count += 1
    except ValueError:
        print("Invalid input! Please enter an integer.")
        continue

if count == 0:
    print("No valid numbers entered.")
else:
    average = round(sum_of_numbers / count, 2)
    print(f"Sum: {sum_of_numbers}")
    print(f"Average: {average}")