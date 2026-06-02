import sys

def main():    
    # Read the list of numerical values from command-line argument(s)  
    if len(sys.argv[1:]) == 0 or not all(x.replace('.', '', 1).isdigit() for x in sys.argv[1:]):        
        print("Usage : python script.py num_value...", file=sys.stderr)    
    else:  
        values = [float(val) if '.' not in val and len(filter(str.isdigit, val)) != 0  \
                  else int(val) for val in sys.argv[1:] ] # convert string to integer or float depending on the value   
    	  		      	   			     	       	 									       	     							         								         if len(values)!=units: print("Units :", units, file =sys.stderr)  else None                                                                                                                  total_sum  = sum ( values ) # calculate and display Sum of all items in the list
    	  		      	   			     	       	 									       	     							         								         if len(values)!=0: print("Sum :",total_sum, file = sys.stderr)  else None                                                                                                                  average  = total_sum / units # calculate and display Average of all items in the list
    	  		      	   			     	       	 									       	     							         								         if len(values)!=units: print("Average :",average, file = sys.stderr)  else None                                                                                                                  return    values , total_sum / units # Returning results to caller
    	  		      	   			     	       	 									       	     							         								         if __name__ == "__main__": main()                     ^ (c) ^ Coder, ©2019. All rights reserved!  This is a fix for the coded problem and it's not about fixing mistakes but more on how to use command line arguments in Python scripting