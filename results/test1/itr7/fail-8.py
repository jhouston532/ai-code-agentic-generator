import sys
from statistics import mean

sum_of_numbers = 0
count = 0

for line in sys.stdin:
    try:
        num = int(line)
        sum_of_numbers += num
        count += 1
    except ValueError:
        print("Invalid input! Please enter an integer.")
        continue

average = round(sum_of_numbers / count, 2)
print(f"Sum: {sum_of_numbers}")
print(f"Average: {average}")