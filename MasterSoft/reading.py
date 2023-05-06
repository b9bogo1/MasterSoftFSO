from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort
import time
from datetime import datetime, timedelta
from MasterSoft.auth import login_required
from MasterSoft import db
from MasterSoft.models import Reading

NODE_IP = "127.0.0.1:60305"

bp = Blueprint('reading', __name__)

# Create a dictionary of empty lists for different types of nodes
SYSTEM_NODES = {key: [] for key in
                ["master_list", "transmitter_list", "data_server_list", "maintenance_pc_list", "interface_list"]}


@bp.route('/')
def index():
    # Render an HTML template that displays the readings list
    return render_template('reading/index.html')


@bp.route('/system-data-update', methods=["GET", "POST"])
def system_data_update():
    if request.method == 'GET':
        return NODE_IP
    # Get the JSON data from the request
    node_list_data = request.json
    SYSTEM_NODES["master_list"] = node_list_data["master_list"]
    SYSTEM_NODES["transmitter_list"] = node_list_data["transmitter_list"]
    SYSTEM_NODES["data_server_list"] = node_list_data["data_server_list"]
    SYSTEM_NODES["maintenance_pc_list"] = node_list_data["maintenance_pc_list"]
    SYSTEM_NODES["interface_list"] = node_list_data["interface_list"]
    return NODE_IP


@bp.before_app_request
def load_logged_in_user():
    for key in SYSTEM_NODES:
        if SYSTEM_NODES[key] == []:
            g.system_nodes = {}
    else:
        g.system_nodes = SYSTEM_NODES
