#!/usr/bin/env python3

import sys

def add(a, b):
    return a + b

sum = 0
mean = None
input_list = []
for line in sys.stdin:
    try:
        num = int(line)
        sum += num
        input_list.append(num)
    except ValueError:
        continue

mean = round((sum / len(input_list)), 2)

print("Sum:", sum)
print("Average:", mean)