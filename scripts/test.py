values = [0.12, 0.11, 0.1, 0.09, 0.0001]


# values = [val * 100 for val in values]

total = sum(values)

norm = [val / total for val in values]

mutl = [1 / (1 - val) for val in norm]

mult = [1 / (1 - (val / sum(values))) for val in values]
print(norm)
print(mutl)
