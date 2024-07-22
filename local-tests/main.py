# pylint: disable=C0301

"""
This script is used to simulate multiple peers in the network. It creates a docker container for each peer and runs the yacy-cf-backend and yacy-cf-frontend and yacy services for each peer.
It also appends to the search history of each peer at regular intervals to simulate search activity. The peers are automatically stopped after 5 minutes.
"""

# Default Modules
import os
import sys
import time
import json
import subprocess
import random
import threading


# Third-Party Modules
import yaml
from tqdm.auto import tqdm
import requests
from lxml import html

# Constants
# !! All the ports are hardcoded for testing purposes. Make sure that the ports are not in use before running the script !!

# Port configurations
BASE_YACY_PORT = 8092  # Port for the server (starting from 8092)
BASE_YACY_SSL_PORT = 8444  # Port for the SSL server (starting from 8444)
BASE_SOCKET_PORT = 8192  # Port for the socket server (starting from 8192)
BASE_BACKEND_PORT = 3002  # Port for the backend (starting from 3002)
BASE_FRONTEND_PORT = 4002  # Port for the frontend (starting from 4002)

# Senior peer check configurations
SENIOR_CHECK_TIMEOUT = (
    60  # Timeout (in seconds) for checking if the peer is a senior peer
)
SENIOR_CHECK_TRIES = (
    5  # Number of tries to check if the peer is a senior peer (60*5 = 5 minutes)
)

# Search configurations
SEARCH_PER_PEER = 10  # Number of searches per peer
SEARCH_FREQUENCY = 30  # Frequency of search activity in seconds

# Simulation configurations
CLOSING_TIME = 120  # Duration (in seconds) to run the simulation


# Define a function to run the shell script in a separate thread
class PeerSimulator:
    """
    Class to simulate peers. Runs x number of peers in separate docker containers. Waits for the peers to start and then appends to the search history of each peer (emulating search activity).
    Automatically stops the peers after 5 minutes.
    """

    def __init__(self, num_peers, auto_whitelist):
        # Number of peers
        self.num_peers = num_peers
        # Auto whitelist
        self.auto_whitelist = auto_whitelist
        # Stop singal for the threads
        self.stop_signal = threading.Event()
        # Empty initial thread
        self.sim_search_thread: threading.Thread = None

    def list_to_dict(self, data):
        """
        Convert list to dictionary
        """

        # Convert data["services"][f"yacy-cf-backend-{index}"]["environment"] to a dictionary by splitting the string by "="
        temp_dict = dict(x.split("=") for x in data)

        return temp_dict

    def dict_to_list(self, data):
        """
        Convert dictionary to list
        """

        # Convert data["services"][f"yacy-cf-backend-{index}"]["environment"] to a list by joining the key and value with "="
        temp_list = [f"{key}={value}" for key, value in data.items()]

        return temp_list

    def check_if_senior_peer(self, index):
        """
        Check if the peer is a senior peer
        """

        # Setup the URL and XPath
        url = f"http://localhost:{BASE_YACY_PORT + index}/Status.html"
        xpath = "/html/body/div[2]/div/div[2]/div[4]/dl/dd"

        # Fetch the value from the website
        try:
            # Fetch the HTML content of the website
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Check if the request was successful

            # Parse the HTML content
            tree = html.fromstring(response.content)

            # Extract the value using XPath
            value = tree.xpath(xpath)

            # Check if the value exists and return it
            if value:
                return value[0].text_content()
            else:
                return "junior or dead"
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the website: {e}")
            return "junior or dead"

    def run_shell_script(self, index, start_stop="1"):
        """
        Run the shell script for the given peer index
        """

        # Get absolute path of the shell script
        shell_script_path = os.path.abspath(f"docker/peer{index}")
        print(f"Running shell script: {shell_script_path}")

        # Run the shell script
        # First argument is the path to bash executable
        # Second argument is the path to the shell script
        # Third argument is the path to the shell script directory (to be used in the shell script)
        # Fourth argument is start or stop (1 for start, 0 for stop)
        result: subprocess.CompletedProcess = subprocess.run(
            [
                r"C:\Program Files\Git\git-bash.exe",
                f"{shell_script_path}/start_peer.sh",
                f"{shell_script_path}",
                start_stop,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        if result.returncode != 0:
            print(f"Error running shell script: {result.stderr}")
        else:
            print(f"Shell script ran successfully. {result.stdout}")

        return result

    def run_container(self, index):
        """
        Run the docker container for the given peer index
        """

        # Create a thread to run the shell script
        thread = threading.Thread(target=self.run_shell_script, args=(index, "1"))
        thread.daemon = True

        # Start the thread
        thread.start()

        return thread

    def stop_container(self, index):
        """
        Stop the docker container for the given peer index
        """

        # Create a thread to run the shell script
        thread = threading.Thread(target=self.run_shell_script, args=(index, "0"))
        thread.daemon = True

        # Start the thread
        thread.start()

        return thread

    def add_histories(self, index):
        """
        Add search histories to the peer
        """

        # From ./histories/dummy_search_history.json pick 4 random items and add them to ./histories/search_history_{index}.json

        # Load the dummy search history
        with open(
            "histories/dummy_search_history_1.json", "r", encoding="UTF-8"
        ) as file:
            data = json.load(file)

        # Pick 4 random items
        search_history = random.sample(data["history"], 4)
        search_history = {"history": search_history}

        if not os.path.exists(f"docker/peer{index}/histories"):
            os.makedirs(f"docker/peer{index}/histories")

        # Save the search history
        with open(
            f"docker/peer{index}/histories/history.json", "w", encoding="UTF-8"
        ) as file:
            json.dump(search_history, file, indent=4)

    def append_one_to_history(self, index):
        """
        Append one random item to the search history
        """

        # Load the search history
        with open(
            f"docker/peer{index}/histories/history.json", "r", encoding="UTF-8"
        ) as file:
            data = json.load(file)

        # Load the dummy search history
        with open(
            "histories/dummy_search_history_1.json", "r", encoding="UTF-8"
        ) as file:
            dummy_data = json.load(file)

        # Pick 1 random item
        while True:
            search_history = random.sample(dummy_data["history"], 1)[0]

            if search_history not in data["history"]:
                break

        # Append the item to the search history
        data["history"].append(search_history)

        # Save the search history
        with open(
            f"docker/peer{index}/histories/history.json", "w", encoding="UTF-8"
        ) as file:
            json.dump(data, file, indent=4)

    def add_whitelist(self, index):
        """
        Add a whitelist to the peer
        """

        whitelist = {"whitelist": []}

        if not os.path.exists(f"docker/peer{index}/whitelist"):
            os.makedirs(f"docker/peer{index}/whitelist")

        with open(
            f"docker/peer{index}/whitelist/whitelist.json", "w", encoding="UTF-8"
        ) as file:
            json.dump(whitelist, file, indent=4)

    def sim_search(self, num_peers):
        """
        Simulate search activity by appending to the search history of each peer
        """

        # Append to the search history of each peer
        # x items for each peer
        try:
            for _ in range(SEARCH_PER_PEER):
                for j in range(num_peers):
                    # Append one random item to the search history
                    self.append_one_to_history(j)

                    # Exit if stop signal is set
                    if self.stop_signal.is_set():
                        return

                time.sleep(SEARCH_FREQUENCY)
        except KeyboardInterrupt:
            print("Keyboard interrupt detected. Stopping the sim.")

        return

    def create_shells(self, index):
        """
        Create the shell scripts for the given peer index
        """

        # Load base shell file
        with open("docker/start_peer.sh", "r", encoding="UTF-8") as file:
            data = file.read()

        data = data.replace("yacy-server", f"yacy-server-{index}")
        data = data.replace("yacy-cf-backend", f"yacy-cf-backend-{index}")
        data = data.replace("yacy-cf-frontend", f"yacy-cf-frontend-{index}")
        data = data.replace(
            "'s/port=8090/port=8091/'", f"'s/port=8090/port={BASE_YACY_PORT + index}/'"
        )
        data = data.replace(
            "'s/port.ssl=8443/port.ssl=8444/'",
            f"'s/port.ssl=8443/port.ssl={BASE_YACY_SSL_PORT + index}/'",
        )
        with open(f"docker/peer{index}/start_peer.sh", "w", encoding="UTF-8") as file:
            file.write(data)

    def create_docker_compose(self, index):
        """
        Create the docker-compose file for the given peer index
        """

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
        data["services"][f"yacy-server-{index}"]["expose"] = [
            f"{BASE_YACY_PORT + index}"
        ]

        # Update the backend port
        data["services"][f"yacy-cf-backend-{index}"]["ports"] = [
            f"{BASE_BACKEND_PORT + index}:{BASE_BACKEND_PORT + index}",
            f"{BASE_SOCKET_PORT + index}:{BASE_SOCKET_PORT + index}",
        ]
        data["services"][f"yacy-cf-backend-{index}"]["expose"] = [
            f"{BASE_BACKEND_PORT + index}",
            f"{BASE_SOCKET_PORT + index}",
        ]

        # Update the backend environment
        temp_env = self.list_to_dict(
            data["services"][f"yacy-cf-backend-{index}"]["environment"]
        )
        temp_env["SERVER_FLASK_PORT"] = f"{BASE_BACKEND_PORT + index}"
        temp_env["SOCKET_PORT"] = f"{BASE_SOCKET_PORT + index}"
        temp_env["YACY_PORT"] = f"{BASE_YACY_PORT + index}"
        temp_env["DEBUG_AUTO_WHITELIST"] = self.auto_whitelist
        temp_env["DEBUG_AUTO_WHITELIST_NUM_NODES"] = self.num_peers
        data["services"][f"yacy-cf-backend-{index}"]["environment"] = self.dict_to_list(
            temp_env
        )

        # Update the frontend port
        data["services"][f"yacy-cf-frontend-{index}"]["ports"] = [
            f"{BASE_FRONTEND_PORT + index}:{BASE_FRONTEND_PORT + index}"
        ]
        data["services"][f"yacy-cf-frontend-{index}"]["expose"] = [
            f"{BASE_FRONTEND_PORT + index}"
        ]

        # Update the frontend environment
        temp_env = self.list_to_dict(
            data["services"][f"yacy-cf-frontend-{index}"]["environment"]
        )
        temp_env["REACT_APP_API_PORT"] = f"{BASE_BACKEND_PORT + index}"
        temp_env["PORT"] = f"{BASE_FRONTEND_PORT + index}"
        data["services"][f"yacy-cf-frontend-{index}"]["environment"] = (
            self.dict_to_list(temp_env)
        )

        if not os.path.exists(f"docker/peer{index}"):
            os.makedirs(f"docker/peer{index}")

        with open(
            f"docker/peer{index}/docker-compose.yml", "w", encoding="UTF-8"
        ) as file:
            yaml.dump(data, file)

    def start_search_sim(self):
        """
        Start the simulation of search activity
        """

        # Create a thread to simulate search activity
        sim_search_thread = threading.Thread(
            target=self.sim_search, args=(self.num_peers,)
        )
        sim_search_thread.daemon = True

        # Start the thread
        sim_search_thread.start()

        return sim_search_thread

    def auto_whitelist_peers(self):
        """
        Automatically whitelist the peers via the backend
        """

        for i in tqdm(
            range(self.num_peers), desc="Auto whitelisting peers", unit="peer"
        ):
            url = f"http://localhost:{BASE_BACKEND_PORT + i}/api/auto_whitelist"

            # Send the request
            try:
                response = requests.get(url, timeout=60)
                response.raise_for_status()  # Check if the request was successful

                tqdm.write(
                    f"Auto whitelist called for peer {i} with port {BASE_BACKEND_PORT + i}"
                )
            except requests.exceptions.RequestException as e:
                tqdm.write(
                    f"Error whitelisting peer {i} with port {BASE_BACKEND_PORT + i}: {e}"
                )

            # Wait for 1 second before sending the next request
            time.sleep(2)

    def wait_for_senior_peer(self, index):
        """
        Wait for the peer to become a senior peer
        """

        with tqdm(
            total=SENIOR_CHECK_TIMEOUT,
            desc=f"Waiting for peer {index} to become senior",
        ) as pbar:
            for i in range(SENIOR_CHECK_TIMEOUT):
                # Check if the peer is a senior peer
                result = self.check_if_senior_peer(index)
                if "senior" in result.lower():
                    # make the pbar reach 100%
                    pbar.update(SENIOR_CHECK_TIMEOUT - i)
                    return True

                time.sleep(1)
                pbar.update(1)

        return False

    def check_if_all_senior_peers(self):
        """
        Check if all the peers are senior peers
        """

        # Wait for the peers to become senior peers
        try:
            for i in range(SENIOR_CHECK_TRIES):
                still_juniors = False
                for i in range(self.num_peers):
                    result = self.wait_for_senior_peer(i)
                    if result:
                        print(f"Peer {i} is a senior peer")
                    else:
                        still_juniors = True
                        print(f"Peer {i} is not a senior peer")

                if not still_juniors:
                    print("All peers are senior peers")
                    return True

                print("Not all peers are senior peers. Retrying...")

            print("Timeout reached. Not all peers are senior peers.")
        except KeyboardInterrupt:
            print("Keyboard interrupt detected. Stopping the sim.")

        return False

    def start_peers(self):
        """
        Start the peers
        """

        print("Starting the peers")

        # Create a list to store the threads
        threads: list[threading.Thread] = []

        # Setup the peers and start the containers
        for i in range(self.num_peers):
            self.create_docker_compose(i)
            self.create_shells(i)
            self.add_histories(i)
            self.add_whitelist(i)
            inc_thread = self.run_container(i)
            threads.append(inc_thread)

        print("All peers start scripts started successfully")
        print("Waiting for shell scripts to finish")
        # Wait for the threads to finish
        for thread in threads:
            thread.join()
            time.sleep(1)

        print("Checking if the peers are senior peers")
        self.check_if_all_senior_peers()

        # Start the simulating search activity
        self.sim_search_thread = self.start_search_sim()

        # Give a head start to the peers, 5 seconds is just a arbitrary number
        time.sleep(5)

        # Auto whitelist the peers
        print("Auto whitelisting the peers")
        self.auto_whitelist_peers()

        # Wait for 5 minutes. Then stop the peers
        with tqdm(total=CLOSING_TIME, desc="Closing in") as pbar:
            for i in range(CLOSING_TIME):
                time.sleep(1)
                pbar.update(1)

        print("Stopping the simulation of search activity")

        # Set the stop signal
        self.stop_signal.set()

        # Stop the sim_search thread
        self.sim_search_thread.join()

        print("Stopping the peers")

        # Stop the containers
        threads: list[threading.Thread] = []

        # Stop the containers hence stopping the peers
        for i in range(self.num_peers):
            inc_thread = self.stop_container(i)
            threads.append(inc_thread)

        print("All peers stop scripts started successfully")
        print("Waiting for shell scripts to finish")

        # Wait for the threads to finish
        for thread in threads:
            thread.join()
            time.sleep(1)

        print("All peers stopped successfully")

    def main(self):
        """
        Main function to update the docker-compose file
        """

        self.start_peers()


def main():
    """
    Main function to update the docker-compose file
    """

    # Get number of peers from args
    num_peers = int(sys.argv[1])
    auto_whitelist = sys.argv[2]

    peer_simulator = PeerSimulator(num_peers, auto_whitelist)
    peer_simulator.main()


if __name__ == "__main__":
    main()
