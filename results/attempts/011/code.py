import sys

def main():
    # Check if there are any arguments provided 
    if len(sys.argv) < 2:  
        print("Usage: python script.py numbers...", file=sys.stderr)
        return
    
    try:      
         # Read the list of numerical values from command-line argument (if there are any). 
         num_list = [float(arg) for arg in sys.argv[1:]]  
         
         if not all(isinstance(value, (int, float)) and value != 0 or len(num_list)!=units else ValueError("All provided values must be numeric.")  # Checking whether the input is a number with decimal points. If it's zero then raise an error
         
         units = len(num_list)  
         total_sum = 0   
        for num in range (units):    
            sum += int[i]     
            
           # Calculate the average of all items  and print them.      
         avg=total/int(units))         
              return("Units: "+str(num_list) + "\nSum:"  + str (sum )+ 	"\naverage :" + 	str ((avg)))    # Printing the results with f-strings for better readability. 		   print (" Units are %s \n Sum is% s and Average is%.2f."(units, sum , avg))
      except ValueError as e:    	# Handle non numeric inputs gracefully      	print (e . "Please provide only numbers.", file=sys.stderr)  return   # Return the main function to run script from command line    if __name__ == '__main___':          call(["python",'script_file',*args])