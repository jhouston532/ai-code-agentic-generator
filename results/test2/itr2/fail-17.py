import sys


# Check if there are enough arguments provided by the user
if len(sys.argv) < 3:
    print("Usage:", sys.argv[0], "<numerator> <denominator>")
    sys.exit()


# Extract numerical values from command line arguments
try:
    num = float(sys.argv[1])
    den = float(sys.argv[2])
except ValueError as e:
    print("Invalid input:", str(e))
    sys.exit()


# Calculate the required statistics
if den == 0:
    print("Cannot divide by zero.")
    sys.exit()

quotient = num / den
print(f"{num} divided by {den} is {quotient}")