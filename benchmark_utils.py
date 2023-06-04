import requests
import itertools
from evalplus.data import get_human_eval_plus, write_jsonl

problems = get_human_eval_plus()
num_samples_per_task = 1

def run(prompt, seed, port = 5000, temperature = 0.1):
    HOST = 'localhost:%s' % port
    URI = f'http://{HOST}/api/v1/generate'

    request = {
        'prompt': prompt,
        'max_new_tokens': 500,
        'do_sample': True,
        'temperature': temperature,
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
        'seed': seed,
        'add_bos_token': True,
        'truncation_length': 2048,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': []
    }

    response = requests.post(URI, json=request)
    if response.status_code == 200:
        result = response.json()['results'][0]['text']
        return prompt + result

def get_function_body(code):
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

def cut_off_prefix(s):
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

def generate_one_completion(prompt_code, seed = -1, port = 5000, prompt_type = "long", user_tag = "HUMAN:", assistant_tag = "AI MODEL:", system_prefix = ""):
    print(seed)
    suffix = 'def'+prompt_code.split("def")[1].split("(")[0]+"("
    
    if prompt_type == "long":
        prompt = """%s
%s
Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

code:
%s

%s
```python
%s""" % (system_prefix, user_tag, prompt_code, assistant_tag, suffix)

    elif prompt_type =="medium":
        prompt = """%s
Please complete the following code:

%s
%s
```python""" % (user_tag, prompt_code, assistant_tag)

    elif prompt_type == "short":
        prompt = """```python
%s""" % prompt_code

    print("####\n"+prompt, "\n####")
    code_result = run(prompt, seed = seed, port = port)
    # result = "\n".join(code_result.split("def")[-1].split("\n")[1:]).split("```")[0]
    # print("---", code_result, "---")
    result = cut_off_prefix(code_result.split("```python")[-1])
    result = get_function_body(result)

    print("***\n"+result, "\n***")
    return result

def run_benchmark(filename, maxnum=-1, port=5000, prompt_type = "long", user_tag = "### Instruction:", assistant_tag = "### Response:", system_prefix = ""):
    filepath = "results/"+filename+"_%s"%prompt_type+".jsonl"
    iterc = itertools.count()
    if maxnum == -1:
        problem_keys = list(problems)
    else:
        problem_keys = list(problems)[:maxnum]
    all_samples = []
    print("Benchmarking and writing to", filepath)
    for idx, task_id in enumerate(problem_keys):
        # Generate real completions
        for _ in range(num_samples_per_task):
            completion = generate_one_completion(problems[task_id]["prompt"], seed=next(iterc), port=port, prompt_type = prompt_type, user_tag = user_tag, assistant_tag = assistant_tag, system_prefix = system_prefix)
            all_samples.append(dict(task_id=task_id, completion=completion))

        # Create a temporary copy of all_samples, to which we will append 'pass' completions
        temp_samples = all_samples.copy()

        # Append 'pass' completions for the rest of the tasks
        for remaining_task_id in list(problems)[idx+1:maxnum] + list(problems)[maxnum:]:
            for _ in range(num_samples_per_task):
                temp_samples.append(dict(task_id=remaining_task_id, completion="    pass"))

        # Write all samples to the file, overwriting it completely
        write_jsonl(filepath, temp_samples)
    print("Done writing to", filepath)
