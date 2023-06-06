# OSS Language Model Programming Evaluations Using the HumanEval+ Python Benchmark

This repo is designed to evaluate OSS language models pulled from the HuggingFace Model Hub by running them against the standardized Python coding benchmark HumanEval+. The tool interacts with these models via the oobabooga text-generation-webui API, which serves as the interface for model interaction and generation of Python code completions.

## Results:

![HumanEvalResultsV1](https://github.com/my-other-github-account/llm-humaneval-benchmarks/assets/82987814/afca3cd5-6e3c-4c94-ada5-a965967ebfcb)

## Functionality

- **Interfacing with HuggingFace Models:** The program leverages the text-generation-webui API to interact with language models pulled from the HuggingFace Model Hub. These models are used for generating Python code completions.

- **Code Completion:** Provides functionality for completing given Python code. Different prompt formatting options (short, medium, long) are provided to facilitate various completion contexts. The completion results are then returned.

- **Benchmarking with HumanEval+:** This tool is designed to run benchmarks using the HumanEval+ standardized Python coding tasks. The `run_benchmark` function generates multiple code completions for different tasks and logs the results in a JSONL file. This enables comprehensive evaluation of a model's performance across various coding tasks.

- **Server Management:** The tool includes functionality for starting a separate server process, which runs an AI model. This process serves as the backend that the script interacts with to generate code completions. The server's output is logged for debugging or record-keeping purposes.

## Usage

You'll need to install evalplus for this (on top of having text-generation-webui installed)
pip install evalplus

The notebooks show how to get this running on AWS SageMaker, run a benchmark, and evaluate benchmark results using the Eval+ evaluation CLI.

Basic usage looks like (you'll need to have the model already downloaded from Huggingface, which you can do easily in the usual text-generation-webui GUI) :

```python
from benchmark_manager import run_benchmark_workflow

# Vicuna prompt style:
run_benchmark_workflow("TheBloke_vicuna-7B-1.1-GPTQ-4bit-128g", 6666, group_size=128,
                           prompt_type="long", user_tag="USER:", 
                           assistant_tag="ASSISTANT:", system_prefix="A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.", experiment_tag="vicuna")
                           
# Alpaca prompt style:
run_benchmark_workflow("TheBloke_wizardLM-7B-GPTQ", 6666, group_size=128,
                           prompt_type="long", user_tag="USER:", 
                           assistant_tag="ASSISTANT:", system_prefix="", experiment_tag="alpaca")
```

More advanced usage if you want to customize your prompt more looks like:

```python
import os, signal
from benchmark_utils import run_benchmark, run, extract_code
from benchmark_manager import start_server

model_name = "TheBloke_wizardLM-7B-GPTQ"
portnum = 6666
group_size=128

server_process = start_server(model_name, portnum, group_size=group_size, 
                              working_directory='text-generation-webui') # Make sure server.py is in working_directory

def my_completion(code, **kwargs):
    prompt = "Complete this code:\n%s\nASSISTANT:" % code
    results = extract_code(run(prompt, port=kwargs["port"]))
    print(results)
    return results

run_benchmark(model_name, port=portnum, custom_completion=my_completion, prompt_type = "custom")

os.kill(server_process.pid, signal.SIGTERM)
```

To run evalplus against your results (more advanced analysis is in 2_Parse_Results.ipynb)

```python
import subprocess

filename = "results/TheBloke_wizardLM-7B-GPTQ_custom.jsonl"

result = subprocess.run(["sudo", "/home/ec2-user/anaconda3/envs/pytorch_p39/bin/evalplus.evaluate",
                "--dataset", "humaneval", "--samples", filename, "--i-just-wanna-run"], 
                        text=True, capture_output=True, check=False)

print(result.stdout, "\n", result.stderr)
```

## References:

https://github.com/evalplus/evalplus

https://github.com/openai/human-eval

https://arxiv.org/abs/2107.03374

https://github.com/oobabooga/text-generation-webui

---
