def main():
    sum_of_numbers = 0
    count = 0

    for line in sys.stdin:
        try:
            num = int(line.strip())
            sum_of_numbers += num
            count += 1
        except ValueError:
            print("Invalid input! Please enter an integer.")

    if count == 0:
        print("No valid numbers entered.")
    else:
        average = round(sum_of_numbers / count, 2)
        print(f"Sum: {sum_of_numbers}")
        print(f"Average: {average}")

if __name__ == "__main__":
    main()