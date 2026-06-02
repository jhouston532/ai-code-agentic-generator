Here's a corrected version of the Python script:

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

To test this script, you can run it with the following command:

```
python task_with_tests.py <<INPUT
10
20
30
40
50
```

This will read the input from stdin and print the results to stdout. The output should match EXPECTED_OUTPUT exactly, including the whitespace at the beginning of each line.