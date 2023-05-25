from threading import Thread
import requests
import json
import time
from MasterSoft.models import Reading
from MasterSoft.local_configs import get_node, get_nodes_list

NODE = get_node()
nodes = get_nodes_list()
CYCLE_TIME = 30  # Time in seconds

SAVE_READING_URL = f"http://{NODE['ip']}:{NODE['port']}/save-reading"

# Create a dictionary of empty lists for different types of nodes
SYSTEM_NODES = {key: [] for key in
                ["master_list", "transmitter_list", "data_server_list", "maintenance_pc_list", "interface_list"]}


def clean_string(s):
    return "".join(c for c in s.lower() if c.isalnum())


class ManageNetworkDataFlow(Thread):
    """A class that manages the network data flow between different nodes."""

    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        """A method that runs in a loop and checks the status and data of each node."""
        global master_hostname_list
        global master_hostname_sorted_tuple
        global SYSTEM_NODES
        # Reset the lists of nodes
        for key in SYSTEM_NODES:
            SYSTEM_NODES[key] = []
        master_hostname_list = []
        while True:
            time.sleep(CYCLE_TIME)
            # Check the status of each node in the network and add it to the corresponding list if it is online
            master_node_list = []
            xmter_node_list = []
            maint_node_list = []
            data_node_list = []
            interface_node_list = []
            local_master_hostname_list = []
            for node in nodes:
                if "Master" in node["hostname"]:
                    node_status_check_url = f"http://{node['ip']}:{node['port']}/system-data-update"
                    # Use a try-except block to handle any request exceptions
                    try:
                        master_node_status_check = requests.get(node_status_check_url)
                        if master_node_status_check.status_code == 200:
                            # Append the node to the corresponding list based on its hostname
                            master_node_list.append(node)
                            SYSTEM_NODES["master_list"].append(node)
                            local_master_hostname_list.append(node["hostname"])
                    except requests.exceptions.RequestException as e:
                        # Handle the exception
                        print(f"No connexion to: {node['ip']}:{node['port']}")

            master_hostname_list = local_master_hostname_list
            # If there is at least one master node online, sort the hostname list and assign power
            # values based on the order
            if len(master_node_list) >= 1:
                # Sort the string list by the cleaned strings and convert to a tuple
                master_hostname_sorted_tuple = tuple(sorted(master_hostname_list, key=clean_string))
                # Update the power value of the current node if it is a master node
                if NODE["hostname"] in master_hostname_sorted_tuple:
                    NODE["power"] = master_hostname_sorted_tuple.index(NODE["hostname"])
                # Update the power values of the other master nodes in the system nodes list
                for node in master_node_list:
                    if node["hostname"] in master_hostname_sorted_tuple:
                        node["power"] = master_hostname_sorted_tuple.index(node["hostname"])
            SYSTEM_NODES["master_list"] = master_node_list
            node_status_check_url = f"http://{NODE['ip']}:{NODE['port']}/system-data-update"
            headers = {"Content-Type": "application/json"}
            master_nodes_list = requests.post(node_status_check_url, data=json.dumps(SYSTEM_NODES), headers=headers)
            if master_nodes_list.status_code == 200:
                if NODE["power"] == 0:
                    for node in nodes:
                        node_status_check_url = f"http://{node['ip']}:{node['port']}/system-data-update"
                        # Use a try-except block to handle any request exceptions
                        try:
                            node_status_check = requests.post(node_status_check_url, data=json.dumps(SYSTEM_NODES),
                                                              headers=headers)
                            if node_status_check.status_code == 200:
                                if "Xmter" in node["hostname"]:
                                    # Append the node to the corresponding list based on its hostname
                                    xmter_node_list.append(node)
                                elif "Maint" in node["hostname"]:
                                    # Append the node to the corresponding list based on its hostname
                                    maint_node_list.append(node)
                                elif "Data" in node["hostname"]:
                                    # Append the node to the corresponding list based on its hostname
                                    data_node_list.append(node)
                                elif "Interface" in node["hostname"]:
                                    # Append the node to the corresponding list based on its hostname
                                    interface_node_list.append(node)
                        except requests.exceptions.RequestException as e:
                            # Handle the exception
                            print(f"No connexion to: {node['ip']}:{node['port']}")
                    SYSTEM_NODES["transmitter_list"] = xmter_node_list
                    SYSTEM_NODES["data_server_list"] = data_node_list
                    SYSTEM_NODES["maintenance_pc_list"] = maint_node_list
                    SYSTEM_NODES["interface_list"] = interface_node_list
                    for master_node in SYSTEM_NODES["master_list"]:
                        master_node_url = f"http://{master_node['ip']}:{master_node['port']}/system-data-update"
                        headers = {"Content-Type": "application/json"}
                        update_master_response = requests.post(master_node_url, data=json.dumps(SYSTEM_NODES),
                                                               headers=headers)
                        if update_master_response.status_code != 200:
                            print(f"Master nodes {master_node['hostname']} not updated")
                    for Xmter in SYSTEM_NODES["transmitter_list"]:
                        node_data = json.dumps({
                            "requestor": NODE["hostname"],
                            "order_num": int(time.time() * 1000000),
                            "request_type": "External"
                        })
                        xmter_data_received = requests.post(f"http://{Xmter['ip']}:{Xmter['port']}/get-reading",
                                                                data=node_data, headers=headers)
                        if xmter_data_received.status_code == 200:
                            reading_from_transmitter = xmter_data_received.json()
                            headers = {"Content-Type": "application/json"}
                            new_reading = json.dumps({
                                "trans_id": reading_from_transmitter["trans_id"],
                                "created_at": reading_from_transmitter["created_at"],
                                "order_num": reading_from_transmitter["order_num"],
                                "requestor_id": reading_from_transmitter["requestor_id"],
                                "temp_1": reading_from_transmitter["temp_1"],
                                "temp_2": reading_from_transmitter["temp_2"],
                                "rtd_1": reading_from_transmitter["rtd_1"],
                                "rtd_2": reading_from_transmitter["rtd_2"],
                                "is_data_transmitted": reading_from_transmitter["is_data_transmitted"]
                            })
                            save_reading = requests.post(SAVE_READING_URL, data=new_reading, headers=headers)
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
