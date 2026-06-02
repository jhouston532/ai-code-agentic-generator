try:
    sum_of_numbers = int(sys.stdin.readline().strip())   # Reads one line from stdin and converts it to an integer (sum). 
    average = round(mean([int(num) for num in sys.stdin]),2 )    # Computes the sum and computes its mean (rounded to 2 decimal places). If invalid numbers are entered by user or other errors occur during execution of code will be printed here as well .
except ValueError:                                      # If not a valid number, raises exception which is caught in try block below.    
    print("Invalid input!")                              # Print error message if invalid numbers are entered by user or other errors occur during execution of code will be printed here as well.  
else:                                                    # Else clause executes only when no exceptions were raised (i.e., valid number was read). 
     print("Sum:", sum_of_numbers, "Average : ", average)    # Prints the results in desired format if valid inputs are provided by user or execution is successful .