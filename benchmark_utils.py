import requests
import itertools
from evalplus.data import get_human_eval_plus, write_jsonl
import os
import json
import sys
import asyncio
import websockets

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
    'temperature': 0.7,
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

import requests
from time import sleep

async def run_async(prompt, seed=-1, port = 443, deterministic = True, host='localhost'):
    # Set the prompt and seed for the current request
    request = {
        'prompt': prompt,
        'seed': seed,
        'max_new_tokens': 250,
        'truncation_length': 2048,
        'skip_special_tokens': True
    }

    if deterministic:
        request['do_sample'] = False
        request['temperature'] = 1
        request['top_p'] = 1
        request['top_k'] = 0
        request['repetition_penalty'] = 1
        request['num_beams'] = 1
        request['early_stopping'] = False

    URI = f'ws://{host}:{port}/api/v1/stream'

    async with websockets.connect(URI, ping_interval=None) as websocket:
        await websocket.send(json.dumps(request))

        response_text = prompt

        while True:
            incoming_data = await websocket.recv()
            incoming_data = json.loads(incoming_data)

            match incoming_data['event']:
                case 'text_stream':
                    response_text += incoming_data['text']
                case 'stream_end':
                    return response_text

def run_sync(prompt, seed=-1, port=443, deterministic=True, host='localhost'):
    return asyncio.run(run_async(prompt, seed, port, deterministic, host))

def run(prompt, seed=-1, port = 443, deterministic = True, host='localhost'):
    # Set the prompt and seed for the current request
    request = {}
    request['prompt'] = prompt
    request['seed'] = seed
    if deterministic:
        request['do_sample'] = False
        request['temperature'] = 1
        request['top_p'] = 1
        request['top_k'] = 0
        request['repetition_penalty'] = 1

    # Set the URI for the request
    URI = f'{host}:{port}/api/v1/generate'
    
    # Set up retry mechanism
    retries = 2
    backoff_factor = 0.1

    for i in range(retries):
        try:
            # Send the request and return the response
            response = requests.post(URI, json=request, timeout=420)
            response.raise_for_status()
            return prompt + response.json()['results'][0]['text']
        except Exception as err:
            print(f"Attempt {i+1} failed. Error: {err}")
            sleep(backoff_factor * (2 ** i))  # Exponential backoff
        except requests.exceptions.RequestException as e:
            # For any other request exception, raise immediately
            raise e
    raise Exception("All attempts failed")

def get_function_body(code):
    # Extract the function body from the provided code
    lines = code.splitlines()
    function_count = 0
    function_lines = []
    
    for line in lines:
        if line.strip().startswith('def '):
            function_count += 1
            if function_count > 6:  # if more than 3 functions start, break the loop
                break
        elif not line.startswith((' ', '\t')) and not line.strip() == '':
            # If a non-empty line does not start with an indent, break the loop
            if function_count > 0:
                break
        if function_count > 0:
            function_lines.append(line)
            
    return '\n'.join(function_lines)

def get_function_body_old(code):
    lines = code.splitlines()
    function_lines = []
    found_def = False

    for line in lines:
        # If 'def ' is found in a line, mark that we've entered the function
        if 'def ' in line:
            found_def = True
            function_lines.append(line)
            continue

        # If we've entered the function, stop including lines when we hit a line that contains text but does not start with a whitespace character
        if found_def and line.strip() != '' and not line.startswith((' ', '\t')):
            break

        # Always include the line in the function lines
        function_lines.append(line)

    return '\n'.join(function_lines)

def cut_off_prefix_old(s):
    idx_from = s.find('from ')
    idx_def = s.find('def ')
    idx_import = s.find('import ')

    # Check if none of the keywords were found
    if idx_from == -1 and idx_def == -1 and idx_import == -1:
        return s

    # Prepare a list of found indices, excluding those where the keyword was not found
    indices = [idx for idx in [idx_from, idx_def, idx_import] if idx != -1]

    # Return the string starting from the earliest found keyword
    return s[min(indices):]

def extract_code_old(code):
    code = cut_off_prefix(code.split("```python")[-1])
    code = get_function_body(code)
    return code

    
def cut_off_prefix(s):
    # Cut off the prefix from the provided string
    indices = [idx for keyword in ['from ', 'def ', 'import '] if (idx := s.find(keyword)) != -1]
    return s[min(indices):] if indices else s

def extract_code(code, assistant_tag, use_old_parser = False):
    if use_old_parser:
        return extract_code_old(code)
    
    if assistant_tag == "":
        try:
            return get_function_body(cut_off_prefix(code.split("```python")[1]))
        except:
            return get_function_body(cut_off_prefix(code))
    # print("***", code, "***")
    try:
        return get_function_body(cut_off_prefix(code.split(assistant_tag)[1].split("```python")[1]))
    except:
        return get_function_body(code.split(assistant_tag)[1])

def generate_one_completion(prompt_code, seed=-1, port=5000, prompt_template="", user_tag="HUMAN:", 
                            assistant_tag="AI MODEL:", host="localhost", insert_func_stub=False, 
                            deterministic=True, use_old_parser = False, use_async = False, **kwargs):
    # Generate a completion for one prompt
    suffix = ""
    if insert_func_stub:
        suffix = 'def'+prompt_code.split("def")[1].split("(")[0]+"("
    prompt = prompt_template.format(PROMPT=prompt_code) + suffix
    # print(prompt)
    if use_async:
        code_result = run_sync(prompt, seed=seed, port=port, deterministic=deterministic, host=host)
    else:
        code_result = run(prompt, seed=seed, port=port, deterministic=deterministic, host=host)

    if code_result == prompt:
        raise Exception("Model doesn't appear to be loaded. Quitting.")

    to_ret = extract_code(code_result, assistant_tag=assistant_tag, use_old_parser = use_old_parser)
    print(to_ret)
    return to_ret

def run_benchmark(filename, prompt_template, maxnum=-1, start_from=0, port=5000, user_tag="", 
                  assistant_tag="", host="localhost", insert_func_stub=False, 
                  custom_completion=generate_one_completion, use_async = False, deterministic=True, use_old_parser = False, **kwargs):

    filepath = f"results/{filename}.jsonl"
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
                    prompt_template=prompt_template,
                    user_tag=user_tag,
                    assistant_tag=assistant_tag,
                    insert_func_stub=insert_func_stub,
                    deterministic=deterministic,
                    host=host,
                    use_old_parser = use_old_parser, 
                    use_async = use_async,
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
        sys.stdout.flush()
        sys.stderr.flush()

    print("Done writing to", filepath)

