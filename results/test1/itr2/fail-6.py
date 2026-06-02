Here's a corrected version of the script:

```python
import statistics as stats

# read input from stdin
input_list = [int(x) for x in sys.stdin]

# compute sum and mean
sum = 0
for num in input_list:
    sum += num
mean = "{:.2f}".format(stats.mean(input_list))

# print results
print("Sum:", sum)
print("Average:", round(float(mean), 2))
```

This script reads a list of integers from stdin (one per line), computes their sum and mean, then prints both values in the format shown in EXPECTED_OUTPUT. The corrected version properly closes the string in line 8 by using the correct syntax.