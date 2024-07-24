# Copyright (c) Microsoft. All rights reserved.

# Sample function to generate a list of Fibonacci numbers
def fibonacci(n):
    fib_list = [0, 1]
    [fib_list.append(fib_list[-1] + fib_list[-2]) for _ in range(2, n)]
    return fib_list[:n]


print(fibonacci(10))
