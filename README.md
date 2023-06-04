# OSS Language Model Programming Evaluations Using the HumanEval+ Python Benchmark

This Python program is designed to evaluate language models pulled from the HuggingFace Model Hub, running them against the standardized Python coding benchmark, HumanEval+. The tool interacts with these models via the text-generation-webui API, which serves as the interface for model interaction and generation of Python code completions.

## Functionality

- **Interfacing with HuggingFace Models:** The program leverages the text-generation-webui API to interact with language models pulled from the HuggingFace Model Hub. These models are used for generating Python code completions.

- **Code Completion:** Provides functionality for completing given Python code. Different prompt formatting options (short, medium, long) are provided to facilitate various completion contexts. The completion results are then returned.

- **Benchmarking with HumanEval+:** This tool is designed to run benchmarks using the HumanEval+ standardized Python coding tasks. The `run_benchmark` function generates multiple code completions for different tasks and logs the results in a JSONL file. This enables comprehensive evaluation of a model's performance across various coding tasks.

- **Server Management:** The tool includes functionality for starting a separate server process, which runs an AI model. This process serves as the backend that the script interacts with to generate code completions. The server's output is logged for debugging or record-keeping purposes.

## Usage

Call the `run_benchmark_workflow` function to start the entire evaluation process. The parameters for this function include the model name, port number, group size, maximum number of tasks, prompt type, and various formatting strings.

Upon execution, a server is started with the provided parameters, and a benchmark is run on the model's code completion capabilities. The resulting data is then saved to a file in the 'results' directory.

For generating a single code completion from a given prompt, use the `generate_one_completion` function.

The notebooks show how to get this running on AWS SageMaker, run a benchmark, and evaluate benchmark results using the Eval+ evaluation CLI.

---
