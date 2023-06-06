import requests
import itertools
from evalplus.data import get_human_eval_plus, write_jsonl
import os
import json

# Load the problem data
problems = get_human_eval_plus()
num_samples_per_task = 1

HOST = 'localhost'
URI = f'http://{HOST}/api/v1/generate'

# Configure the request parameters
request = {
    'prompt': '',
    'max_new_tokens': 500,
    'do_sample': True,
    'temperature': 0.1,
    'top_p': 0.1,
    'typical_p': 1,
    'epsilon_cutoff': 0,  # In units of 1e-4
    'eta_cutoff': 0,  # In units of 1e-4
    'repetition_penalty': 1.18,
    'top_k': 40,
    'min_length': 0,
    'no_repeat_ngram_size': 0,
    'num_beams': 1,
    'penalty_alpha': 0,
    'length_penalty': 1,
    'early_stopping': False,
    'mirostat_mode': 0,
    'mirostat_tau': 5,
    'mirostat_eta': 0.1,
    'seed': '',
    'add_bos_token': True,
    'truncation_length': 2048,
    'ban_eos_token': False,
    'skip_special_tokens': True,
    'stopping_strings': []
}

def run(prompt, seed=-1, port = 5000, deterministic = True):
    # Set the prompt and seed for the current request
    request['prompt'] = prompt
    request['seed'] = seed
    if deterministic:
        request['do_sample'] = False
        request['temperature'] = 1
        request['top_p'] = 1
        request['top_k'] = 0
        request['repetition_penalty'] = 1

    # Set the URI for the request
    URI = f'http://{HOST}:{port}/api/v1/generate'
    # Send the request and return the response
    response = requests.post(URI, json=request)
    return prompt + response.json()['results'][0]['text'] if response.status_code == 200 else ''

def get_function_body(code):
    # Extract the function body from the provided code
    lines = code.splitlines()
    start_function = False
    function_lines = []
    
    for line in lines:
        if line.strip().startswith('def '):
            if start_function:  # if a new function starts, break the loop
                break
            start_function = True
        elif not line.startswith((' ', '\t')) and not line.strip() == '':
            # If a non-empty line does not start with an indent, break the loop
            if start_function:
                break
        if start_function:
            function_lines.append(line)
            
    return '\n'.join(function_lines)

def cut_off_prefix(s):
    # Cut off the prefix from the provided string
    indices = [idx for keyword in ['from ', 'def ', 'import '] if (idx := s.find(keyword)) != -1]
    return s[min(indices):] if indices else s

def generate_prompt(prompt_code, suffix, prompt_type, user_tag, assistant_tag, system_prefix):
    # Generate a prompt based on the provided parameters
    prompts = {
        "long": """%s
%s
Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

code:
%s

%s
```python
%s""" % (system_prefix, user_tag, prompt_code, assistant_tag, suffix),
        "medium": """%s\nPlease complete the following code:\n%s\n%s\n```python""" % (user_tag, prompt_code, assistant_tag),
        "short": """```python\n%s""" % prompt_code,
        "very_short": """%s\n\t""" % prompt_code
    }
    return prompts[prompt_type]

def extract_code(code):
    try:
        return get_function_body(cut_off_prefix(code.split("```python")[1]))
    except:
        return get_function_body(cut_off_prefix(code.split("```python")[-1]))

def generate_one_completion(prompt_code, seed = -1, port = 5000, prompt_type = "long", user_tag = "HUMAN:", assistant_tag = "AI MODEL:", system_prefix = "", deterministic = True, **kwargs):
    # Generate a completion for one prompt
    suffix = 'def'+prompt_code.split("def")[1].split("(")[0]+"("
    prompt = generate_prompt(prompt_code, suffix, prompt_type, user_tag, assistant_tag, system_prefix)
    code_result = run(prompt, seed = seed, port = port, deterministic = deterministic)
    to_ret = extract_code(code_result)
    print(to_ret)
    return to_ret


def run_benchmark(filename, maxnum=-1, start_from=0, port=5000, prompt_type = "long",
                  user_tag = "", assistant_tag = "",
                  system_prefix = "", experiment_tag = "", custom_completion=generate_one_completion, deterministic = True, **kwargs):

    filepath = f"results/{filename}_{prompt_type}_{experiment_tag}.jsonl"
    print("Results will be written to:", filepath)
    problem_keys = list(problems) if maxnum == -1 else list(problems)[:maxnum]

    all_samples, iterc = [], itertools.count()

    if not os.path.exists("results"):
            os.makedirs("results")

    # If start_from is greater than 0, load existing data
    if start_from > 0:
        with open(filepath, 'r') as file:
            existing_data = [json.loads(line) for line in file]
            all_samples = existing_data[:start_from*num_samples_per_task]
            last_task_id = all_samples[-1]['task_id'] if all_samples else None
            start_it = problem_keys.index(last_task_id) + 1 if last_task_id else 0
            problem_keys = problem_keys[start_it:]

    for idx, task_id in enumerate(problem_keys, start=start_from):
        print("Processing Task", idx, "of", len(list(problems)))
        for _ in range(num_samples_per_task):
            # Prepare parameters for custom completion
            params = {
                'task_id': task_id,
                'completion': custom_completion(
                    problems[task_id]["prompt"],
                    seed=next(iterc),
                    port=port,
                    prompt_type=prompt_type,
                    user_tag=user_tag,
                    assistant_tag=assistant_tag,
                    system_prefix=system_prefix,
                    deterministic=deterministic,
                    **kwargs
                )
            }
            all_samples.append(params)

        # Always add placeholders for remaining problems
        remaining_keys = problem_keys[idx+1:]
        placeholders = [dict(task_id=remaining_task_id, completion="    pass") 
                        for remaining_task_id in remaining_keys
                        for _ in range(num_samples_per_task)]
        temp_samples = all_samples + placeholders

        # Write to the file, overwriting previous data
        with open(filepath, 'w') as file:
            for item in temp_samples:
                file.write(json.dumps(item) + '\n')

    print("Done writing to", filepath)

