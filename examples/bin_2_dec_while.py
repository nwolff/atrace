binaire = [1, 0, 1, 0, 1, 0]
décimal = 0

while binaire:
    bit = binaire.pop(0)
    décimal = 2 * décimal + bit

print(décimal)
