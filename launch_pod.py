import json
import subprocess
import threading
import sys
import time
from benchmark_utils import run_benchmark

def get_output_and_retry(call_string, max_retries=5):
    for attempt in range(max_retries):
        result = get_ipython().getoutput(f'curl -s --request POST {call_string}')
        data_dict = json.loads(result[-1])
        print(data_dict)
        if "INTERNAL_SERVER_ERROR" not in str(data_dict):
            return data_dict
        else:
            print(f"ERROR - Attempt {attempt+1}, Retrying in 5s")
            time.sleep(5)
    raise Exception(f"Failed after {max_retries} attempts")

def launch_pod(api_key, gpu_type, pod_num):

    gpu_count = 1
    if gpu_type[:2] == "2x":
        gpu_type = gpu_type[2:]
        gpu_count = 2

    call_string = f"""--header 'content-type: application/json' \
  --url 'https://api.runpod.io/graphql?api_key={api_key}' \
  --data '{{"query": "mutation {{ podFindAndDeployOnDemand( input: {{ cloudType: SECURE, gpuCount: {gpu_count}, volumeInGb: 100, containerDiskInGb: 10, minVcpuCount: 2, minMemoryInGb: 20, gpuTypeId: \\"{gpu_type}\\", name: \\"RunPod TextGenWebUI #{pod_num}\\", imageName: \\"succulentsteve/webui:latest\\", dockerArgs: \\"\\", ports: \\"7860/http,5000/http,22/tcp,5005/tcp\\", volumeMountPath: \\"/workspace\\", env: [] }} ) {{ id imageName env machineId machine {{ podHostId }} }} }}"}}'"""

    result = get_ipython().getoutput(f'curl -s --request POST {call_string}')
    data_dict = get_output_and_retry(call_string, max_retries=5)
    pod_id = data_dict['data']['podFindAndDeployOnDemand']['id']
    machine_id = data_dict['data']['podFindAndDeployOnDemand']['machineId']
    host_id = machine_id = data_dict['data']['podFindAndDeployOnDemand']['machine']['podHostId']
    return pod_id, machine_id, host_id

def wait_for_pod(pod_id, api_key):
    curl_command = f"""curl -s --request POST \
    --header 'content-type: application/json' \
    --url 'https://api.runpod.io/graphql?api_key={api_key}' \
    --data '{{"query": "query Pod {{ pod(input: {{podId: \\"{pod_id}\\"}}) {{ id name runtime {{ uptimeInSeconds ports {{ ip isIpPublic privatePort publicPort type }} gpus {{ id gpuUtilPercent memoryUtilPercent }} container {{ cpuPercent memoryPercent }} }} }} }}"}}'"""
    while True:
        result = get_ipython().getoutput(curl_command)
        data = json.loads(result[-1])
        try:
            port_22_info = [port for port in data["data"]["pod"]["runtime"]["ports"] if port["type"] == "tcp" and port["privatePort"] == 22]
            ssh_ip = port_22_info[0]["ip"]
            ssh_port = port_22_info[0]["publicPort"]

            port_5005_info = [port for port in data["data"]["pod"]["runtime"]["ports"] if port["type"] == "tcp" and port["privatePort"] == 5005]
            ws_ip = port_5005_info[0]["ip"]
            ws_port = port_5005_info[0]["publicPort"]

            return ssh_ip, ssh_port, ws_ip, ws_port
        except:
            print("not ready yet")
            time.sleep(10)

def download_model(ssh_ip, ssh_port, model):
    model_file = model.replace("/", "_")
    cmd = f"'cd /root/text-generation-webui && python download-model.py --output /workspace/models {model}'"
    get_ipython().system(f'ssh -o StrictHostKeyChecking=no root@{ssh_ip} -p {ssh_port} -i ~/.ssh/id_ed25519 {cmd}')
    return model_file

def swap_gptq(ssh_ip, ssh_port):
    commands = [
    "cd /workspace && git clone -n https://github.com/qwopqwop200/GPTQ-for-LLaMa",
    "ln -s /workspace/GPTQ-for-LLaMa /root/text-generation-webui/repositories/GPTQ-for-LLaMa"
    ]
    for cmd in commands:
        get_ipython().system(f'ssh -o StrictHostKeyChecking=no root@{ssh_ip} -p {ssh_port} -i ~/.ssh/id_ed25519 {cmd}')

def remove_safetensors(ssh_ip, ssh_port, model_file, model_wget_path):
    cmd = f"'cd /workspace/models/{model_file} && rm -rf *.safetensors && wget -q {model_wget_path}'"
    get_ipython().system(f'ssh -o StrictHostKeyChecking=no root@{ssh_ip} -p {ssh_port} -i ~/.ssh/id_ed25519 {cmd}')

import time

import threading
from concurrent.futures import ThreadPoolExecutor, Future

def run_ssh_command(command, pod_id, api_key):

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True)
    server_started = threading.Event()

    def stdout_thread(process):
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            print(line)
            sys.stdout.flush()
            if "Running on local URL" in line:
                server_started.set()

    def stderr_thread(process):
        for line in iter(process.stderr.readline, ''):
            print(line.strip(), file=sys.stderr)
            sys.stderr.flush()
            if "Connection to " in line:
                stop_and_terminate_pod(pod_id, api_key)
                raise Exception(line)

    threading.Thread(target=stdout_thread, args=(process,), daemon=True).start()
    threading.Thread(target=stderr_thread, args=(process,), daemon=True).start()

    def check_timeout(timeout, event):
        time.sleep(timeout * 60)  # Timeout in minutes
        if not event.is_set():
            raise Exception('Timeout exceeded')

    timeout_thread = threading.Thread(target=check_timeout, args=(5, server_started), daemon=False)
    timeout_thread.start()

    while not server_started.is_set():
        time.sleep(1)
        if not timeout_thread.is_alive():
            raise Exception('Timeout exceeded')

    print("continuing")

    sys.stdout.flush()
    sys.stderr.flush()



def run_pod_server(ssh_ip, ssh_port, model_file, gptq_params, pod_id, api_key, use_autoq = False, additional_cmd=""):
    auto = ""
    if use_autoq:
        auto = "--autogptq"
    try:
        command = f"""ssh -tt -o StrictHostKeyChecking=no root@{ssh_ip} -p {ssh_port} -i ~/.ssh/id_ed25519 'cd /root/text-generation-webui && python server.py --listen --api --model {model_file} --model-dir /workspace/models {gptq_params} {additional_cmd} --trust-remote-code --auto-devices {auto} --model_type "Llama"'"""
        print(command)
        run_ssh_command(command, pod_id, api_key)
        print("Done")
    except Exception as e:
        print(f"An error occurred: {e}")

def launch_webui(api_key, api_url='https://api.runpod.io/graphql', model="TheBloke/wizard-vicuna-13B-GPTQ", gptq_params="", gpu_type="NVIDIA RTX A4000", pod_num="1", url_replace_safetensors = None, use_new_gptq = False, use_autoq = False, additional_cmd="", use_async = False):
    pod_id, machine_id, host_id = launch_pod(api_key, gpu_type, pod_num)
    ssh_ip, ssh_port, ws_ip, ws_port = wait_for_pod(pod_id, api_key)
    url = "https://%s-7860.proxy.runpod.net" % pod_id
    api_url = "https://%s-5000.proxy.runpod.net" % pod_id
    ssh = "ssh -o StrictHostKeyChecking=no %s@ssh.runpod.io -i ~/.ssh/id_ed25519" % machine_id
    print("WebUI:", url, "API", api_url, "SSH", ssh, sep="\n")
    print("\n\n")
    
    if use_new_gptq:
        swap_gptq(ssh_ip, ssh_port)
    
    model_file = download_model(ssh_ip, ssh_port, model)
    
    if url_replace_safetensors is not None:
        print("Removing safetensors...")
        remove_safetensors(ssh_ip, ssh_port, model_file, url_replace_safetensors)
    run_pod_server(ssh_ip, ssh_port, model_file, gptq_params, pod_id, api_key, use_autoq=use_autoq, additional_cmd=additional_cmd)
    if use_async:
        return api_url, model_file, pod_id, ws_ip, ws_port
    return api_url, model_file, pod_id

def pod_benchmark(filename, prompt, assistant_tag, pod_id, api_key, start_from=0,
                      host="http://localhost", port=5000, insert_func_stub=True, use_old_parser = False, deterministic=True, use_async = False):
    import time

    while True:
        try:
            run_benchmark(filename, prompt, start_from=start_from,
                          host=host, port=port, insert_func_stub=insert_func_stub, assistant_tag=assistant_tag, use_old_parser = use_old_parser, deterministic=deterministic, use_async = use_async)
            break  # If the function executes without raising an exception, exit the loop
        except Exception as e:
            # Check if the first argument of the exception is a tuple and the second element of the tuple is 404
            if isinstance(e.args[0], tuple) and e.args[0][1] == 404:
                # Retry the operation after waiting for some time
                print("Caught 404 error. Retrying after 5 seconds...")
                time.sleep(5)
            else:
                # Reraise the exception if it's not the specific one we're handling
                stop_and_terminate_pod(pod_id, api_key)
                raise

def stop_pod(pod_id, api_key):
    stop_pod_command = f"""curl --request POST \
    --header 'content-type: application/json' \
    --url 'https://api.runpod.io/graphql?api_key={api_key}' \
    --data '{{"query": "mutation {{ podStop(input: {{podId: \\"{pod_id}\\"}}) {{ id desiredStatus }} }}"}}'"""
    get_ipython().system('{stop_pod_command}')

def terminate_pod(pod_id, api_key):
    terminate_pod_command = f"""curl --request POST \
    --header 'content-type: application/json' \
    --url 'https://api.runpod.io/graphql?api_key={api_key}' \
    --data '{{"query": "mutation {{ podTerminate(input: {{podId: \\"{pod_id}\\"}}) }}"}}'"""
    get_ipython().system('{terminate_pod_command}')

def stop_and_terminate_pod(pod_id, api_key):
    stop_pod(pod_id, api_key)
    terminate_pod(pod_id, api_key)
    
def killall_pods(api_key):
    cmd = """curl -s --request POST \
  --header 'content-type: application/json' \
  --url 'https://api.runpod.io/graphql?api_key=%s' \
  --data '{"query": "query Pods { myself { pods { id name runtime { uptimeInSeconds ports { ip isIpPublic privatePort publicPort type } gpus { id gpuUtilPercent memoryUtilPercent } container { cpuPercent memoryPercent } } } } }"}'""" % api_key
    result = get_ipython().getoutput(cmd)
    # Parse the JSON string
    data = json.loads("".join(result))

    # Extract pod ids
    pod_ids = [pod['id'] for pod in data['data']['myself']['pods']]

    for pid in pod_ids:
        stop_and_terminate_pod(pid, api_key)