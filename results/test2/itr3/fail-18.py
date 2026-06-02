import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 script.py numbers...", file=sys.stderr)
        return

    try:         # Try to convert command line arguments into float values 
        values = [float(i) for i in sys.argv[1:]]  

        if len(values) == 0 :                   # Checking whether there are any numeric inputs or not, else print error message and exit from the program        
            raise ValueError("No Numerical values provided") 

    except ValueError as e:                    # Catch exception in case of wrong input format (non-numerics)  
        print(f"Invalid Input. Please provide only numeric inputs.\n{e}", file=sys.stderr)    

    else :                                   # If no exceptions occurred, then proceed to calculate units and sum 

      num_units = len(values)                # Calculate number of items (Units: N)  
      total_sum = sum(values)                  # Calculate the sum using built-in sum function
      average = total_sum / num_units        # Calculate average  (Average is Sum divided by number of items)   

      print(f"Units: {num_units}")
      print(f"Sum: {total_sum}")
      print(f"Average: {average:.2f}")

if __name__ == "__main__":
    main()