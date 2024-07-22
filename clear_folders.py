import requests
import sys
import shutil

def clear_histories(peer_num):
    """
    Clear the histories of the peer
    """

    # Delete the history folder of the peer
    path_to_history = f"docker/peer{peer_num}/histories"
    shutil.rmtree(path_to_history)

def clear_evaluation(peer_num):
    """
    Clear the evaluation of the peer
    """

    # Delete the evaluation folder of the peer
    path_to_evaluation = f"docker/peer{peer_num}/evaluation_results"
    shutil.rmtree(path_to_evaluation)


def main():

    # Get number of peers from args
    num_peers = int(sys.argv[1])

    # Update the docker-compose file
    for i in range(num_peers):
        clear_histories(i)
        clear_evaluation(i)

if __name__ == "__main__":
    main()