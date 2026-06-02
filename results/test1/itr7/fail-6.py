import sys   # Importing the system module for handling command line arguments in Python   
from statistics import mean     # Statistics error raised when no numeric value is found (mean function) was imported from 'statistical' library to handle exceptions if invalid inputs are entered by user or other errors occur during execution. 
  
try:      # Try block will catch any exception in case of non-numerics values, empty lines and so on which might be present when reading stdin (user input).   
     sum_of_numbers = int(sys.stdin.readline().strip())       # Reads one line from sys module's standard input stream to an integer type variable 'sum'. 
except ValueError:        # If not a valid number, raises exception which is caught in try block below   .   
     print("Invalid Input!")      # Print error message if invalid numbers are entered by user or other errors occur during execution.      
else :                   # Else clause executes only when no exceptions were raised (i.e., a valid number was read). 
        sum_of_numbers = int(sys.stdin.readline().strip())   # Reads one more line from sys module's standard input stream to an integer type variable 'sum'.   
                                                                # This is done because the previous exception block will have already raised a ValueError for first read, so we need another try-except here  .    
        average = round(mean([int(num) for num in sys.stdin]),2 )   # Computes sum and computes its mean (rounded to two decimal places). If invalid numbers are entered by user or other errors occur during execution, it will be printed below as well  .   
print("Sum:",sum_of_numbers,"Average : ",average)      # Prints the results in desired format if valid inputs provided (by users and/or code executions).