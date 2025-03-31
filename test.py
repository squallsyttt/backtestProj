def add_numbers(x,y):
    print(f"Adding {x} to {y}")
    result = x + y

    print(f"Result is {result}")
    return result

def main(x0,y0):
    x1 = x0*3
    y1 = y0*4
    return add_numbers(x1,y1)

#测试
a = 5
b = 7
c = main(a,b)

print(f"3x{a} + 4x{b} = {c}")