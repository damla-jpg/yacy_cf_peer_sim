import requests
import sys

def add_whitelist(peer_num):
    """
    Add a whitelist to the peer
    """

    peer_num = peer_num + 2
    requests.get(f"http://localhost:300{peer_num}/api/auto_whitelist", timeout=60)
    print(f"Whitelist for peer {peer_num} created successfully")

def main():

    # Get number of peers from args
    num_peers = int(sys.argv[1])

    # Update the docker-compose file
    for i in range(num_peers):
        add_whitelist(i)

if __name__ == "__main__":
    main()