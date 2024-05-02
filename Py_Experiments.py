import torch
import transformers

from transformers import BitsAndBytesConfig
# from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model
# from trl import SFTTrainer, DataCollatorForCompletionOnlyLM
# from datasets import load_dataset

# import numpy as np
# import pandas as pd
from tqdm import tqdm
import re, sys, subprocess, gc
# from collections import Counter, defaultdict

from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig


# https://huggingface.co/docs/peft/main/en/developer_guides/quantization

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type='nf4',
    bnb_4bit_compute_dtype=torch.bfloat16,
)


# Load in the model
model_id = "nvidia/OpenMath-Mistral-7B-v0.1-hf"
tokenizer = AutoTokenizer.from_pretrained(model_id)
if torch.cuda.is_available():
    print("cuda")
    model = AutoModelForCausalLM.from_pretrained(model_id, 
                                                device_map="cuda:0", 
                                                quantization_config=quantization_config, 
                                                pad_token_id=tokenizer.eos_token_id)
elif torch.backends.mps.is_available():
    print("mps")
    model = AutoModelForCausalLM.from_pretrained(model_id,
                                                 device_map="mps",
                                                 pad_token_id=tokenizer.eos_token_id)
else:
    print("cpu")
    model = AutoModelForCausalLM.from_pretrained(model_id,
                                                 pad_token_id=tokenizer.eos_token_id)
    
model.eval()
print(tokenizer.eos_token_id)
pipeline = transformers.pipeline("text-generation", model=model, tokenizer=tokenizer, torch_dtype='auto', device_map="auto")

tokenizer.pad_token = tokenizer.eos_token
tokenizer.add_eos_token = True
tokenizer.add_bos_token, tokenizer.add_eos_token
tokenizer.padding_side = "left"


############ DATA ##############
import random
from format_data import get_data_SFTTrainer
from rag import get_RAG_context
# from trl import SFTTrainer, DataCollatorForCompletionOnlyLM
from sklearn.feature_extraction.text import TfidfVectorizer


train_dataset = get_data_SFTTrainer('data/math/merged_math_problems_train_clean.json')
random.shuffle(train_dataset)

split = 0.8
train_dataset = train_dataset[:int(split*len(train_dataset))]
val_dataset = train_dataset[int(split*len(train_dataset)):]
test_dataset = get_data_SFTTrainer('data/math/merged_math_problems_test_clean.json')


########## RAG ###############
#TODO: Additional prompt engineering to clean up just appending RAG context to the start
text_format = """### Question: {problem_statement}"""

# RAG support
prompts = [example["prompt"] for example in train_dataset] 
vectorizer = TfidfVectorizer()                       # Initialize TF-IDF vectorizer
tfidf_matrix = vectorizer.fit_transform(prompts)     # Fit vectorizer on prompts
RAG_params = {
    "train_data": train_dataset,
    "vectorizer": vectorizer,
    "tfidf_matrix": tfidf_matrix,
}
TOP_K = 1

def formatting_prompts_func(dataset):
    output_texts = []
    for question_dict in tqdm(dataset):
        problem = question_dict["prompt"]
        text = text_format.format(problem_statement=problem)
        # get RAG-supported context
        context = get_RAG_context(question_dict, top_k=TOP_K, RAG_params = RAG_params)
        output_texts.append(context+text)
    return output_texts
rag_formatted_test_dataset = formatting_prompts_func(test_dataset)
rag_formatted_test_dataset[0:2]


#### ANSWER EXTRACTION ######
def naive_parse(answer):
    out = []
    start = False
    end = False
    for l in reversed(list(answer)):
        if l in '0123456789' and not end:
            start = True
            out.append(l)
        else:
            if start:
                end = True
        
    out = reversed(out)
    return ''.join(out)

def process_output(output): 
    result = output
    try:
        code = output.split('```')[1][7:]
        with open('code.py', 'w') as fout:
            fout.write(code)
        batcmd = 'timeout 7 ' + sys.executable + ' code.py'
        try:
            shell_output = subprocess.check_output(batcmd, shell=True).decode('utf8')
            code_output = round(float(eval(shell_output))) % 1000
        except:
            code_output = -1
    except Exception as e:
        code_output = -1
    try:
        result_output = re.findall(r'\\boxed\{(.*)\}', result)
        if not len(result_output):
            result_output = naive_parse(result)
        else:
            result_output = result_output[-1]
        if not len(result_output):
            result_output = -1
        else:
            result_output = round(float(eval(result_output))) % 1000
    except Exception as e:
        result_output = -1
    return result_output, code_output



####### TESTING ########
tool_instruction = " The answer should be given as a non-negative modulo 1000."
tool_instruction += '\nPlease integrate natural language reasoning with programs to solve the problem above, and put your final answer within \\boxed{}.'
n_repetitions = 1 #5
total_results = []
total_answers = []

for i in tqdm(range(len(rag_formatted_test_dataset[:10]))):
    problem = rag_formatted_test_dataset[i]
    messages = [{"role": "user", "content": problem + tool_instruction}]
    query_prompt = tokenizer.apply_chat_template(messages, tokenize=False)
    results = []
    answers = []
    for _ in range(n_repetitions):
        try:
            raw_output = pipeline(query_prompt, max_new_tokens=2048, do_sample=True, temperature=0.8911, return_full_text=False)
            raw_output = raw_output[0]['generated_text']
            #print(raw_output)
            result_output, code_output = process_output(raw_output)
            torch.cuda.empty_cache()
            gc.collect()
        except Exception as e:
            print("caught error:", e)
            result_output, code_output = -1, -1
        results.append(result_output)
        answers.append(code_output)
    total_results.append(results)
    total_answers.append(answers)

print(total_answers)
print(total_results)
problem = rag_formatted_test_dataset[0]
# problem = test_dataset[0]['prompt']
print(problem)

# token_input = tokenizer.encode(query_prompt, return_tensors='pt')
# output = model.generate(token_input, max_length=5000, num_return_sequences=1, temperature=0.7)
# generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
# print(token_input[-1])
# print(generated_text)

print(pipeline(problem, max_new_tokens=2048, do_sample=True, temperature=0.8911, return_full_text=False))

