import subprocess
import os
import signal
import threading
from benchmark_utils import generate_one_completion, run_benchmark

def print_server_output(process):
    """
    This function prints the output of a subprocess in real-time.
    
    :param process: The subprocess whose output should be printed.
    """
    for line in process.stdout:
        print(line, end='')


def start_server(model_name, portnum, group_size=None, wbits=None, working_directory='text-generation-webui', public = False):
    """
    This function starts a server in a new process.
    
    :param model_name: The name of the model to be used by the server.
    :param portnum: The base port number to be used by the server.
    :param group_size: The group size to be used by the server.
    :param working_directory: The working directory in which the server script resides.
    :return: The subprocess in which the server is running.
    """
    # Create the base command list
    command = [
        'python', 'server.py', 
        '--api', 
        '--api-blocking-port', str(portnum), 
        '--api-streaming-port', str(portnum+1),  
        '--listen-port', str(portnum+2), 
        '--model_type', 'llama',
        '--trust-remote-code'
    ]
    
    if model_name is not None:
        command += ['--model', model_name]
    
    if wbits is not None:
        command += ['--wbits', str(wbits),]
        
    if public:
        command += ['--share']

    # If group_size is provided, append it to the command list
    if group_size is not None:
        command += ['--groupsize', str(group_size)]

    print("Starting server...")
    
    # Start the server in a new process
    server_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=working_directory)

    # Wait for "Starting API" to be printed before proceeding
    for line in iter(server_process.stdout.readline, ''):
        print(line, end='')  # Optionally print the server output
        if "Starting API" in line:
            break

    print("Server started!")
    
    return server_process

def block_log_server(server_process):
    for line in iter(server_process.stdout.readline, ''):
        print(line, end='')
        
def run_benchmark_workflow(model_name, portnum, group_size=None, wbits=4,
                           maxnum=-1, start_from=0, 
                           prompt_type="long", user_tag="### Instruction:", 
                           assistant_tag="### Response:", system_prefix="", experiment_tag="", 
                           working_directory='text-generation-webui', public=False):
    """
    This function manages the complete benchmark workflow, including starting the server, running the benchmark, and stopping the server.
    
    :param model_name: The name of the model to be used.
    :param portnum: The base port number to be used by the server.
    :param group_size: The group size to be used by the server.
    :param maxnum: The maximum number of items to process during the benchmark.
    :param prompt_type: The type of prompt to use during the benchmark.
    :param user_tag: The user tag to use during the benchmark.
    :param assistant_tag: The assistant tag to use during the benchmark.
    :param system_prefix: The system prefix to use during the benchmark.
    :param experiment_tag: The experiment tag to use during the benchmark.
    :param working_directory: The working directory in which the server script resides.
    """
    # Start the server
    server_process = start_server(model_name, portnum, wbits = wbits, group_size=group_size, working_directory=working_directory, public=public)

    # Create a separate thread to print the server output
    print_thread = threading.Thread(target=print_server_output, args=(server_process,))
    print_thread.start()

    # Run the benchmark
    run_benchmark(model_name, maxnum=maxnum, start_from=start_from,
              port=portnum, prompt_type=prompt_type, user_tag=user_tag,
              assistant_tag=assistant_tag, experiment_tag=experiment_tag, system_prefix=system_prefix)

    # Once the benchmark has finished running, terminate the server process
    os.kill(server_process.pid, signal.SIGTERM)
    
    # Wait for the print_thread to finish
    print_thread.join()
