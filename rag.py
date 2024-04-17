import pprint
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from format_data import get_data_SFTTrainer

########### IMPLEMENTING IN OUR LOGIC on Test set #####################
def get_RAG_context(question_obj, RAG_params, top_k):
    """
    retrives similar questions/solutions as the prompt in question_obj to be used for ICL
    Args:
        question_obj: dict of {'prompt': _, 'completion':_}
        RAG_params: dict {
            "train_data": train_data,
            "vectorizer": vectorizer,
            "tfidf_matrix": tfidf_matrix,
        }
        top_k: how many similar questions/solutions user wants for context
    """
    # extrac RAG params
    train_data = RAG_params["train_data"]
    vectorizer = RAG_params["vectorizer"]
    tfidf_matrix = RAG_params["tfidf_matrix"]

    # get and vectorize the query
    query = question_obj["prompt"]
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



if __name__ == "__main__":
    # Get Retrieval data from training dataset
    # this should be done outside the test eval loop
    train_data = get_data_SFTTrainer('data/math/merged_math_problems_train_clean.json')
    prompts = [example["prompt"] for example in train_data] 
    vectorizer = TfidfVectorizer()                       # Initialize TF-IDF vectorizer
    tfidf_matrix = vectorizer.fit_transform(prompts)     # Fit vectorizer on prompts
    RAG_params = {
        "train_data": train_data,
        "vectorizer": vectorizer,
        "tfidf_matrix": tfidf_matrix,
    }

    # Example of use
    test_data = get_data_SFTTrainer('data/math/merged_math_problems_test_clean.json') # list
    test_question_obj=test_data[0]
    print("TEST QUESTION")
    print(test_question_obj["prompt"])
    print()
    print("CONTEXT")
    print(get_RAG_context(test_question_obj, RAG_params, top_k=3))
    print()



