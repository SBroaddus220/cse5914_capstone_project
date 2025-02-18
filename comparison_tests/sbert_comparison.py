from bert_score import score
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def tag_lists_similarity(lists) -> float:
    """
    Compares lists and returns a similarity value in [0, 1]
    'lists' is a list of lists of strings
    """
    n = len(lists)
    if (n < 2): return 1.0

    total_similarity = 0.0
    for i in range(n - 1):
        for j in range(i + 1, n):
            if i == j: break
            total_similarity += compare_lists(lists[i], lists[j])
    
    num_combinations = n * (n-1) / 2
    avg_similarity = total_similarity / num_combinations
    return avg_similarity

def compare_lists(l1, l2) -> float:
    """
    Compares two lists of varied length and returns similarity value in [0, 1]
    l1 and l2 are lists of strings
    """
    total_similarity = _compare_list_to_list(l1, l2) + _compare_list_to_list(l2, l1)
    avg_similarity = total_similarity / 2
    return avg_similarity

def _compare_list_to_list(fixed, aligned) -> float:
    """
    Compares 'fixed' and 'aligned' lists by aligning 'aligned' with elements of 'fixed', returning a similarity value in [0, 1]
    Asymetric binary operation, a helper method (so treat as private)
    'fixed' and 'aligned' are lists of strings
    """
    n = len(fixed)
    total_similarity = 0.0

    for i in range(n):
        aligned_similarity = 0.0
        for j in range(len(aligned)):
            candidate_similarity = compare_words(fixed[i], aligned[j])
            if candidate_similarity > aligned_similarity: aligned_similarity = candidate_similarity
        total_similarity += aligned_similarity

    avg_similarity = total_similarity / n
    return avg_similarity

def compare_words(w1, w2) -> float:
    """
    Compares words w1 and w2 with BERT and returns a similarity in [0, 1]
    w1 and w2 are strings
    """
    embedding1 = model.encode([w1])
    embedding2 = model.encode([w2])

    # Compute cosine similarity
    similarity = cosine_similarity(embedding1, embedding2)
    return similarity[0][0]



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
    print(f"{list} similarity is {round(tag_lists_similarity(list), 3)}")