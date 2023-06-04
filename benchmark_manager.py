import subprocess
import os
import signal
import threading
from benchmark_utils import generate_one_completion, run_benchmark

def print_server_output(process):
    for line in process.stdout:
        print(line, end='')

def run_benchmark_workflow(model_name, portnum, group_size=None, maxnum=-1, 
                           prompt_type="long", user_tag="### Instruction:", 
                           assistant_tag="### Response:", system_prefix="", experiment_tag=""):
    # Create the base command list
    command = ['python', 'server.py', '--api', '--model', model_name, '--api-blocking-port', str(portnum), '--api-streaming-port', str(portnum+1),  '--listen-port', str(portnum+2), '--wbits', str(4)]

    # If group_size is not None, append it to the command list
    if group_size is not None:
        command += ['--groupsize', str(group_size)]

    print("Starting server...")
    # Start server.py in a separate process
    server_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, cwd='text-generation-webui')

    # Wait for "Starting API" to be printed before running the benchmark
    for line in iter(server_process.stdout.readline, ''):
        print(line, end='')  # Optionally print the server output
        if "Starting API" in line:
            break

    print("Server started!")

    # Create a separate thread to print the server output
    print_thread = threading.Thread(target=print_server_output, args=(server_process,))
    print_thread.start()

    # Run the benchmark
    run_benchmark(model_name+"_"+experiment_tag, maxnum, portnum, prompt_type, user_tag, assistant_tag, system_prefix)

    # Once the benchmark has finished running, kill the server process
    os.kill(server_process.pid, signal.SIGTERM)
    # Wait for the print_thread to finish
    print_thread.join()
