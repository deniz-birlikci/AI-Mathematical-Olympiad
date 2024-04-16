import json
from util import clean_latex, get_clean_path
"""
Cleans and formats merged_math and AMC/AIME json data for SFTTrainer
"""

def format_math_problems(data_path, is_amc=False):
    """
    format single file into {"prompt": ..., "completion":...}
    data_path: single data path of where data is stored
    returns list of dicts {"prompt": ..., "completion":...}
    """
    all_problems_formatted = []

    # load the json array and take first element
    with open(data_path) as f:
        math_data_json_list = json.load(f)
        for math_data_json in math_data_json_list:
            if is_amc:
                # different json format
                all_problems_formatted.append({
                "prompt": clean_latex(math_data_json["problem"]), 
                "completion": clean_latex(math_data_json["solutions"][0]["solution"])
                })
            else:
                all_problems_formatted.append({
                    "prompt": clean_latex(math_data_json["problem"]), 
                    "completion": clean_latex(math_data_json["solution"])
                })

    return all_problems_formatted


def create_formatted_json(data_path, is_amc=False):
    """
    go through data path, cleans data, stores as new json file
    args:
        - data_paths: list of paths where data is stored 
    """
    new_path = get_clean_path(data_path)
    # Open a file in write mode
    with open(new_path, 'w') as f:
        json.dump(format_math_problems(data_path, is_amc), f, indent=4)


def get_data_SFTTrainer(data_path):
    """
    load data in proper format for SFTTrainer module
    returns formatted data as list of dicts {"prompt": ..., "completion":...}
    """
    # load the json array and take first element
    with open(data_path) as f:
        math_data_json_list = json.load(f)

    return math_data_json_list         
   