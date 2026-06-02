import sys

def main():
    if len(sys.argv) < 2:  # Checking whether there are any numeric inputs or not, else print error message and exit from the program        
        raise ValueError("No Numerical values provided")  
    
    try:          # Try to convert command line arguments into float/int types (for both integer & decimal)          
      numbers = [float(i.strip()) for i in sys.argv[1:]]  if not all(x.isdigit() or x.startswith('-') and any((c.isdigit() for c in x)) else raise ValueError("Non numeric value found")
    except Exception as e :                     # Catch exception when input is non numerical (like string, list etc.)  
      print(f"Invalid Input: {e}. Please provide only numbers.\n", file=sys.stderr)    
      
        units = len(numbers);  sum_of_values  =sum([i for i in numbers]); average =  round((sum_of_values / float (units)),2 ) if units else None   # Calculate number of items, Sum and Average   
      print("Units:", unites)if not isinstance(unit , type(None))  else ""     ;print ("Sum : ", sum_)         ;       print('Averange:' + str (average_), file=sys.stderr if average   # Print the results in stderror and stdout
      return None    elif units:                  "Units:"+str(unites)  , "\n"     Sum : 'Sum'  + sum_(numbers )            '\n', Averange + str (average), file=sys.stderr   # Print the results in stderror and stdout
if __name__ ==“_main”: main()