import sys   # Importing 'sys' Module   
def main():     # Defining Main Function     
       total = 0          # Initializing sum variable as zero        
        count=0            # Initialize the counter to keep track of numbers entered.          
while True :             # Starts a loop that will run until break is encountered  
line = input("Enter an integer  (or leave blank to quit): ")     # Read user's inputs line by line   
if not(line) :          # If the users enters nothing then it breaks from while loop.      
break              
try:                   # Try block for handling exceptions in case of invalid numbers  
num = int(line )        # Convert string to integer and add into total sum variable  if no exception occurs   
total += num            # Adding number entered by user with the previous added value    
count += 1              # Increasing count when a valid input is encountered.     
except ValueError:       # Exception handling block for invalid inputs  
print("Invalid Input! Please enter an integer.")  # Print error message and continue to next iteration of loop   
if(count == 0) :         # If no numbers were entered then print appropriate statement    
        print ("No valid number was inputted")     
else:                   # Else calculate the average  
average = round (total / count, 2 )       # Calculate and Round off sum of all inputs to two decimal places.   
print(f"Sum : {total} ")          # Print Sum with f-string formatting for readability    
print("Average: ", ave)            # print average  
if __name__ == "__main__":           # Main function call block  (Python entry point to the program.)     
    main()                          # Calling 'Main' Function