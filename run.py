from waitress import serve
import MasterSoft
from MasterSoft.local_configs import get_node

NODE = get_node()

if __name__ == "__main__":
    serve(MasterSoft.create_app(), host=NODE['ip'], port=NODE['port'])
