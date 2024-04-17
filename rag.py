import pprint
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from format_data import get_data_SFTTrainer

# Get Retrieval data from training dataset
train_data = get_data_SFTTrainer('data/math/merged_math_problems_train_clean.json')
prompts = [example["prompt"] for example in train_data] 

# Initialize TF-IDF vectorizer
vectorizer = TfidfVectorizer()
# Fit vectorizer on prompts
tfidf_matrix = vectorizer.fit_transform(prompts)

########### IMPLEMENTING IN OUR LOGIC on Test set #####################
test_data = get_data_SFTTrainer('data/math/merged_math_problems_test_clean.json') # list
def get_RAG_context(question_obj, top_k):
    query = question_obj["prompt"]
    # Vectorize the query
    query_vector = vectorizer.transform([query])

    # Calculate cosine similarity between query and prompts
    similarities = cosine_similarity(query_vector, tfidf_matrix)

    # Sort prompts by similarity
    similar_problems_indices = similarities.argsort()[0][::-1]

    # Retrieve top similar prompts -> this is the (unformatted) context we pass in
    similar_problem_objs = [train_data[i] for i in similar_problems_indices[:top_k]]

    # transform similar_problem_objs into context
    # "prompt: "...
    # "completion: "...
    context = ""
    for similar_problem_obj in similar_problem_objs:
        prompt = similar_problem_obj["prompt"]
        completion = similar_problem_obj["completion"]
        context += "prompt: {} \ncompletion: {}\n".format(prompt, completion)

    context += "prompt: "
    return context



## Example 
if __name__ == "__main__":
    question_obj=test_data[0]
    print("TEST QUESTION")
    print(question_obj["prompt"])
    print()
    print("CONTEXT")
    print(get_RAG_context(question_obj, top_k=3))
    print()



