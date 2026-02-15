
input_data = """
GWN-00476-10450-ASCB-7769
GWN-00476-10200-ASCB-8130
GWN-00476-10800-ASCB-8205
GWN-00476-10200-ASCB-8676
GWN-00476-10650-ASCB-4593
"""


lines = [line.strip() for line in input_data.strip().splitlines() if line.strip()]
output = ',\n'.join(f'"{line}"' for line in lines)


print(output)
