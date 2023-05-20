from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort
import time
from datetime import datetime, timedelta
from MasterSoft.auth import login_required
from MasterSoft import db
from MasterSoft.models import Reading
from MasterSoft.local_configs import get_node

NODE = get_node()

NODE_IP = f"{NODE['ip']}:{NODE['port']}"
MASTER_NAME = f"{NODE['hostname']}"
MAX_INTERNAL_LIMIT = 6

bp = Blueprint('reading', __name__)

# Create a dictionary of empty lists for different types of nodes
SYSTEM_NODES = {key: [] for key in
                ["master_list", "transmitter_list", "data_server_list", "maintenance_pc_list", "interface_list"]}


@bp.route('/')
@login_required
def index():
    # Render an HTML template that displays the readings list
    return render_template('reading/index.html')


@bp.route('/system-data-update', methods=["GET", "POST"])
def system_data_update():
    global NODE
    node = get_node()
    if request.method == 'GET':
        return NODE_IP
    # Get the JSON data from the request
    node_list_data = request.json
    SYSTEM_NODES["master_list"] = node_list_data["master_list"]
    SYSTEM_NODES["transmitter_list"] = node_list_data["transmitter_list"]
    SYSTEM_NODES["data_server_list"] = node_list_data["data_server_list"]
    SYSTEM_NODES["maintenance_pc_list"] = node_list_data["maintenance_pc_list"]
    SYSTEM_NODES["interface_list"] = node_list_data["interface_list"]
    for master_node in SYSTEM_NODES["master_list"]:
        if master_node["hostname"] == node["hostname"]:
            NODE = master_node
            g.node = master_node
    return NODE_IP


@bp.route('/save-reading', methods=["POST"])
def save_reading():
    reading_to_save = request.json
    # Create a new Reading object with the sensor data and the requestor data
    new_reading = Reading(
        trans_id=reading_to_save["trans_id"],
        created_at=reading_to_save["created_at"],
        order_num=reading_to_save["order_num"],
        requestor_id=reading_to_save["requestor_id"],
        temp_1=reading_to_save["temp_1"],
        temp_2=reading_to_save["temp_2"],
        rtd_1=reading_to_save["rtd_1"],
        rtd_2=reading_to_save["rtd_2"],
        is_data_transmitted=reading_to_save["is_data_transmitted"]
    )
    # Add the new Reading object to the database session
    db.session.add(new_reading)
    # Commit the changes to the database
    db.session.commit()
    # Get the latest reading from the database or None if no row is found
    reading = Reading.query.order_by(Reading.created_at.desc()).first()
    reading_dict = reading.as_dict()  # convert the Reading object to a dictionary
    json_object = jsonify(reading_dict)  # convert the dictionary to a JSON object
    # print(reading_dict['id'])
    # print(json_object.get_json())
    return json_object


@bp.route('/save-unsaved-readings', methods=["POST"])
def save_unsaved_readings():
    unsaved_readings = request.json
    print(f"Unsaved Readings | {unsaved_readings}")
    return jsonify(unsaved_readings)


@bp.route('/internal-reading-list', methods=['GET'])
def internal_reading_list():
    # Get the latest readings from the database up to the limit
    last_readings = Reading.query.order_by(Reading.created_at.desc()).limit(MAX_INTERNAL_LIMIT).all()
    # Create an empty list to store the reading dictionaries
    local_readings = []
    local_system_nodes = []
    # Loop through each reading object
    for reading in last_readings:
        # Convert the row to a dictionary using the as_dict method
        reading_dict = reading.as_dict()
        # Convert the datetime object to a string using isoformat method with timespec argument
        reading_dict["created_at"] = reading_dict["created_at"].isoformat(timespec="seconds")
        # Append the reading dictionary to the data list
        local_readings.append(reading_dict)
        # Return a JSON response with the data list
    return jsonify({"readings": local_readings, "nodes": SYSTEM_NODES, "node": NODE})


@bp.route('/handle-non-transmitted-readings/<int:time_range>', methods=['GET'])
def hdl_non_transmitted_readings(time_range):
    # # get the current time
    # now = datetime.now()
    # # get the time 10 minutes ago
    # ten_minutes_ago = now - timedelta(minutes=time_range)
    # # Create an empty list to store the reading dictionaries
    data = []
    # # query the Reading table and filter by created_at and is_data_transmitted columns
    # non_transmitted_readings = db.session.query(Reading) \
    #     .filter(Reading.created_at >= ten_minutes_ago, Reading.is_data_transmitted == False).all()
    # # Loop through each reading object
    # for reading in non_transmitted_readings:
    #     # Convert the row to a dictionary using the as_dict method
    #     reading_dict = reading.as_dict()
    #     # Convert the datetime object to a string using isoformat method with timespec argument
    #     reading_dict["created_at"] = reading_dict["created_at"].isoformat(timespec="microseconds")
    #     # Append the reading dictionary to the data list
    #     data.append(reading_dict)
    #     # Return a JSON response with the data list
    return jsonify(data)


@bp.route('/get-latest-reading-saved', methods=['GET'])
def latest_reading_saved():
    # reading = Reading.query.order_by(Reading.created_at.desc()).first()
    # if reading is None:
    #     # Return a 404 Not Found error with a message
    #     return jsonify({"error": "No reading found"}), 404
    # reading_dict = reading.as_dict()
    # # Convert the datetime object to a string using isoformat method
    # reading_dict["created_at"] = reading_dict["created_at"].isoformat(timespec="microseconds")
    return jsonify({})
    # return jsonify(reading_dict)


@bp.route('/get-nodes-list', methods=["GET", "POST"])
def get_nodes_list():
    for key in SYSTEM_NODES:
        if SYSTEM_NODES[key] == []:
            return None
        else:
            return g.system_nodes


@bp.before_app_request
def load_system_nodes():
    for key in SYSTEM_NODES:
        if SYSTEM_NODES[key] == []:
            g.system_nodes = {}
        else:
            g.system_nodes = SYSTEM_NODES
