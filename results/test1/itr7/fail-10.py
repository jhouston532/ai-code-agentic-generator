import sys
from statistics import mean

sum_of_numbers = 0 # Initialize the variable to hold total of numbers.
count =  0    #Initiate count for number read from stdin . 
while True:    
    line=sys.stdin.readline().strip()      # Read a string input (one integer per line).      
    if not line : break                    # If no more lines, exit the loop and end program gracefully with an error message to stderr  
                                          
    try: num = int(line)                   # Try converting it into Integer. 
        sum_of_numbers += num              # Adding number in 'sum' variable .     
        ++count                    # Increment count for every read integer input from stdin    
                                         
except ValueError : print("Invalid Input! Please enter an valid Number.")   continue    if (len(sys.argv) - 1 == count): break      
average = round((sum_of_numbers / float(count)),2 ) # Calculate and Round the average .      Printing sum & Average in required format     print("Sum: ",rounded Sum, "Average :", rounded Avg,"\n")  (none) stderr:(None),