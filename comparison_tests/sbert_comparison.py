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