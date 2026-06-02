def main():
    numbers = []
    while True:
        try:
            line = input()
            if line:
                numbers.append(int(line))
            else:
                break
        except EOFError:
            break
    
    total_sum = sum(numbers)
    mean = total_sum / len(numbers)
    
    print("Sum:", total_sum)
    print("Average: {:.2f}".format(mean))

if __name__ == "__main__":
    main()