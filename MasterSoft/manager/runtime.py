from threading import Thread
import requests
import json
import time
import os

NODE = {
    "ip": "127.0.0.1:60305",
    "hostname": "Master-FSO",
    "site": "FSO",
    "power": -1
}

# Create a dictionary of empty lists for different types of nodes
SYSTEM_NODES = {key: [] for key in
                ["master_list", "transmitter_list", "data_server_list", "maintenance_pc_list", "interface_list"]}

# get the MasterSoft directory of the script`
MasterSoft_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(MasterSoft_dir, "system_nodes_local")


def clean_string(s):
    return "".join(c for c in s.lower() if c.isalnum())


# Load the nodes data from a file using requests' JSON decoder
with open(file_path) as nodes_file:
    nodes = json.load(nodes_file)


class ManageNetworkDataFlow(Thread):
    """A class that manages the network data flow between different nodes."""

    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        """A method that runs in a loop and checks the status and data of each node."""
        global master_hostname_list
        global master_hostname_sorted_tuple
        while True:
            # Reset the lists of nodes
            for key in SYSTEM_NODES:
                SYSTEM_NODES[key] = []
                master_hostname_list = []
            time.sleep(5)
            # Check the status of each node in the network and add it to the corresponding list if it is online
            for node in nodes:
                if "Master" in node["hostname"]:
                    node_status_check_url = f"http://{node['ip']}/system-data-update"
                    # Use a try-except block to handle any request exceptions
                    try:
                        master_node_status_check = requests.get(node_status_check_url)
                        if master_node_status_check.status_code == 200:
                            # Append the node to the corresponding list based on its hostname
                            SYSTEM_NODES["master_list"].append(node)
                            master_hostname_list.append(node["hostname"])
                    except requests.exceptions.RequestException as e:
                        # Handle the exception
                        print(f"No connexion to: {node['ip']}")
            # If there is at least one master node online, sort the hostname list and assign power
            # values based on the order
            if len(SYSTEM_NODES["master_list"]) >= 1:
                # Sort the string list by the cleaned strings and convert to a tuple
                master_hostname_sorted_tuple = tuple(sorted(master_hostname_list, key=clean_string))
                # Update the power value of the current node if it is a master node
                if NODE["hostname"] in master_hostname_sorted_tuple:
                    NODE["power"] = master_hostname_sorted_tuple.index(NODE["hostname"])
                # Update the power values of the other master nodes in the system nodes list
                for node in SYSTEM_NODES["master_list"]:
                    if node["hostname"] in master_hostname_sorted_tuple:
                        node["power"] = master_hostname_sorted_tuple.index(node["hostname"])
            node_status_check_url = f"http://{NODE['ip']}/system-data-update"
            headers = {"Content-Type": "application/json"}
            master_nodes_data = json.dumps(SYSTEM_NODES)
            master_nodes_list = requests.post(node_status_check_url, data=master_nodes_data, headers=headers)
            if master_nodes_list.status_code == 200:
                if NODE["power"] == 0:
                    for node in nodes:
                        node_status_check_url = f"http://{node['ip']}/system-data-update"
                        # Use a try-except block to handle any request exceptions
                        try:
                            master_node_status_check = requests.get(node_status_check_url)
                            if master_node_status_check.status_code == 200:
                                if "Xmter" in node["hostname"]:
                                    # Append the node to the corresponding list based on its hostname
                                    SYSTEM_NODES["transmitter_list"].append(node)
                                elif "Maint" in node["hostname"]:
                                    # Append the node to the corresponding list based on its hostname
                                    SYSTEM_NODES["maintenance_pc_list"].append(node)
                                elif "Data" in node["hostname"]:
                                    # Append the node to the corresponding list based on its hostname
                                    SYSTEM_NODES["data_server_list"].append(node)
                                elif "Interface" in node["hostname"]:
                                    # Append the node to the corresponding list based on its hostname
                                    SYSTEM_NODES["interface_list"].append(node)
                        except requests.exceptions.RequestException as e:
                            # Handle the exception
                            print(f"No connexion to: {node['ip']}")
                    node_status_check_url = f"http://{NODE['ip']}/system-data-update"
                    headers = {"Content-Type": "application/json"}
                    online_nodes = json.dumps(SYSTEM_NODES)
                    online_nodes_list = requests.post(node_status_check_url, data=online_nodes, headers=headers)
                    if online_nodes_list.status_code == 200:
                        for Xmter in SYSTEM_NODES["transmitter_list"]:
                            node_data = json.dumps({
                                "requestor": NODE["hostname"],
                                "order_num": int(time.time() * 1000000),
                                "request_type": "External"
                            })
                            headers = {"Content-Type": "application/json"}
                            xmter_data_received = requests.post(f"http://{Xmter['ip']}/get-reading",
                                                                data=node_data, headers=headers)
                            if xmter_data_received.status_code == 200:
                                print(f"Data received from {Xmter['ip']}")
                elif NODE["power"] == 1:
                    pass
                elif NODE["power"] == 2:
                    pass
                elif NODE["power"] == 3:
                    pass
                elif NODE["power"] == 4:
                    pass
                else:
                    pass
                print(f"master nodes updated for node {master_nodes_list.text}")
