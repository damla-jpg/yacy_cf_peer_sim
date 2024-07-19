# Default Modules
import os
import sys
import time
import json
import yaml
import subprocess
import random

BASE_YACY_PORT = 8092
BASE_YACY_SSL_PORT = 8444
BASE_SOCKET_PORT = 8192
BASE_BACKEND_PORT = 3002
BASE_FRONTEND_PORT = 4002

def list_to_dict(data):
    '''
    Convert list to dictionary
    '''

    # Convert data["services"][f"yacy-cf-backend-{index}"]["environment"] to a dictionary by splitting the string by "="
    temp_dict = dict(
        x.split("=") for x in data
    )

    return temp_dict

def dict_to_list(data):
    '''
    Convert dictionary to list
    '''

    # Convert data["services"][f"yacy-cf-backend-{index}"]["environment"] to a list by joining the key and value with "="
    temp_list = [
        f"{key}={value}" for key, value in data.items()
    ]

    return temp_list

def create_shells(index):
    '''
    Create the shell scripts for the given peer index
    '''

    # Load base shell file
    with open("docker/start_peer.sh", "r", encoding="UTF-8") as file:
        data = file.read()

    data = data.replace("yacy-server", f"yacy-server-{index}")
    data = data.replace("yacy-cf-backend", f"yacy-cf-backend-{index}")
    data = data.replace("yacy-cf-frontend", f"yacy-cf-frontend-{index}")
    data = data.replace("'s/port=8090/port=8091/'", f"'s/port=8090/port={BASE_YACY_PORT + index}/'")
    data = data.replace("'s/port.ssl=8443/port.ssl=8444/'", f"'s/port.ssl=8443/port.ssl={BASE_YACY_SSL_PORT + index}/'")
    with open(f"docker/peer{index}/start_peer.sh", "w", encoding="UTF-8") as file:
        file.write(data)

def create_docker_compose(index, auto_whitelist, num_peers):
    '''
    Create the docker-compose file for the given peer index
    '''

    # Load base docker-compose file
    with open("docker/docker-compose.yml", "r", encoding="UTF-8") as file:
        data = file.read()

    data = data.replace("yacy-server", f"yacy-server-{index}")
    data = data.replace("yacy-cf-backend", f"yacy-cf-backend-{index}")
    data = data.replace("yacy-cf-frontend", f"yacy-cf-frontend-{index}")

    # Load the yaml file
    data = yaml.safe_load(data)

    # Update the name
    data["name"] = f"peer{index}"

    # Update the yacy port
    data["services"][f"yacy-server-{index}"]["ports"] = [
        f"{BASE_YACY_PORT + index}:{BASE_YACY_PORT + index}",
        f"{BASE_YACY_SSL_PORT + index}:{BASE_YACY_SSL_PORT + index}",
    ]
    data["services"][f"yacy-server-{index}"]["expose"] = [f"{BASE_YACY_PORT + index}"]

    # Update the backend port
    data["services"][f"yacy-cf-backend-{index}"]["ports"] = [
        f"{BASE_BACKEND_PORT + index}:{BASE_BACKEND_PORT + index}",
        f"{BASE_SOCKET_PORT + index}:{BASE_SOCKET_PORT + index}",
    ]
    data["services"][f"yacy-cf-backend-{index}"]["expose"] = [
        f"{BASE_BACKEND_PORT + index}",
        f"{BASE_SOCKET_PORT + index}",
    ]

    # Update the backend environment\
    temp_env = list_to_dict(data["services"][f"yacy-cf-backend-{index}"]["environment"])
    temp_env["SERVER_FLASK_PORT"] = f"{BASE_BACKEND_PORT + index}"
    temp_env["SOCKET_PORT"] = f"{BASE_SOCKET_PORT + index}"
    temp_env["YACY_PORT"] = f"{BASE_YACY_PORT + index}"
    temp_env["DEBUG_AUTO_WHITELIST"] = auto_whitelist 
    temp_env["DEBUG_AUTO_WHITELIST_NUM_NODES"] = num_peers
    data["services"][f"yacy-cf-backend-{index}"]["environment"] = dict_to_list(temp_env)

    # Update the frontend port
    data["services"][f"yacy-cf-frontend-{index}"]["ports"] = [f"{BASE_FRONTEND_PORT + index}:{BASE_FRONTEND_PORT + index}"]
    data["services"][f"yacy-cf-frontend-{index}"]["expose"] = [f"{BASE_FRONTEND_PORT + index}"]
    
    # Update the frontend environment
    temp_env = list_to_dict(data["services"][f"yacy-cf-frontend-{index}"]["environment"])
    temp_env["REACT_APP_API_PORT"] = f"{BASE_BACKEND_PORT + index}"
    temp_env["PORT"] = f"{BASE_FRONTEND_PORT + index}"
    data["services"][f"yacy-cf-frontend-{index}"]["environment"] = dict_to_list(temp_env)

    if not os.path.exists(f"docker/peer{index}"):
        os.makedirs(f"docker/peer{index}")

    with open(f"docker/peer{index}/docker-compose.yml", "w", encoding="UTF-8") as file:
        yaml.dump(data, file)

def run_container(index):
    '''
    Run the docker container for the given peer index
    '''

    # Change directory to the peer folder
    os.chdir(f"docker/peer{index}")

    # Run the shell script
    result = subprocess.run([r'C:\Program Files\Git\git-bash.exe', "start_peer.sh"], capture_output=True, text=True, check=True)

    # Check the return code
    if result.returncode == 0:
        print("Shell script executed successfully.")
    else:
        print(f"Shell script failed with return code {result.returncode}.")

    # Change directory back to the root folder
    os.chdir("../..")

def add_histories(index):
    '''
    Add search histories to the peer
    '''

    # From ./histories/dummy_search_history.json pick 4 random items and add them to ./histories/search_history_{index}.json

    # Load the dummy search history
    with open("histories/dummy_search_history_1.json", "r", encoding="UTF-8") as file:
        data = json.load(file)

    # Pick 4 random items
    search_history = random.sample(data["history"], 4)
    search_history = {
        "history": search_history
    }

    if not os.path.exists(f"docker/peer{index}/histories"):
        os.makedirs(f"docker/peer{index}/histories")
    
    # Save the search history
    with open(f"docker/peer{index}/histories/history.json", "w", encoding="UTF-8") as file:
        json.dump(search_history, file, indent=4)

def add_whitelist(index):

    whitelist = {
        "whitelist": []
    }

    if not os.path.exists(f"docker/peer{index}/whitelist"):
        os.makedirs(f"docker/peer{index}/whitelist")

    with open(f"docker/peer{index}/whitelist/whitelist.json", "w", encoding="UTF-8") as file:
        json.dump(whitelist, file, indent=4)


def main():
    """
    Main function to update the docker-compose file
    """

    # Get number of peers from args
    num_peers = int(sys.argv[1])
    auto_whitelist = int(sys.argv[2])

    # Update the docker-compose file
    for i in range(num_peers):
        create_docker_compose(i, auto_whitelist, num_peers)
        create_shells(i)
        add_histories(i)
        add_whitelist(i)
        run_container(i)


if __name__ == "__main__":
    main()
