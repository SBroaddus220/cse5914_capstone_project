import sbert_comparison

a1 = ["human"]
a2 = ["person"]

b1 = ["bear"]
b2 = ["bare"]
b3 = ["bruin"]

c1 = ["laundry basket"]
c2 = ["laundry room"]
c3 = ["laundry_basket"]
c4 = ["laundry_room"]

d1 = ["red", "orange"]
d2 = ["red", "yellow"]
d3 = ["orange", "yellow"]
d4 = ["blue", "green", "purple"]
d5 = ["hippopotamus"]

e1 = ["restaurant", "sandwich"]
e2 = ["food", "cafe"]

A1 = [a1, a2]
B1 = [b1, b2]
C1 = [c1, c2]
C2 = [c3, c4]
D1 = [d1, d2]
D2 = [d1, d2, d3]
D3 = [d1, d2, d4]
D4 = [d1, d2, d5]
E1 = [e1, e2]

for list in [D1, D2, D3, D4]:
    print(f"{list} similarity is {round(sbert_comparison.tag_lists_similarity(list), 3)}")