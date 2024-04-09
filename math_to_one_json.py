import json
import os
from tqdm import tqdm

def merge_json_files(base_path):
    json_paths = []
    for topic_dir in os.listdir(base_path):
        topic_path = os.path.join(base_path, topic_dir)
        print(topic_path)
        if os.path.isdir(topic_path):
            for file in os.listdir(topic_path):
                if file.endswith('.json'):
                    print(file)
                    json_paths.append(os.path.join(topic_path, file))

    all_problems = []
    for file_path in tqdm(json_paths, desc="Loading JSON files"):
        with open(file_path, 'r') as json_file:
            problem = json.load(json_file)
            all_problems.append(problem)

    return all_problems

# Assuming the base path is 'MATH/'
merged_problems = merge_json_files('data/math/train/')

# Save the merged problems to a final json file
with open('merged_math_problems_train.json', 'w') as outfile:
    json.dump(merged_problems, outfile, indent=4)

# Assuming the base path is 'MATH/'
merged_problems = merge_json_files('data/math/test/')

# Save the merged problems to a final json file
with open('merged_math_problems_test.json', 'w') as outfile:
    json.dump(merged_problems, outfile, indent=4)