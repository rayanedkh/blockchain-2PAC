import json
from data_struct import Block1,Vote1,Block2,Vote2,Elect,Leader
import base64
from sign import send_signed



    
def to_json(obj,node):
    '''Fonction pour générer les messages au format json à partir des différents types d'objets'''
    base64_representation = base64.b64encode(node.publickey.encode()).decode('utf-8')
    if isinstance(obj, Block1):
        data = {
            'sender': obj.sender,
        }
        return json.dumps({
            'sim_number': node.simulation_number,
            'type': 'Block1',
            'data': data,
            'signature': send_signed(data,node.privatekey),
            'public_key': base64_representation
        })
    elif isinstance(obj, Block2):
        data = {
            'sender': obj.sender,  
            'qc': obj.qc
        }
        return json.dumps({
            'sim_number': node.simulation_number,
            'type': 'Block2',
            'data': data,
            'signature': send_signed(data,node.privatekey),
            'public_key': base64_representation
        })
    elif isinstance(obj, Vote1):
        data = {
            'sender': obj.sender,
            'Block_sender': obj.block_sender
        }
        return json.dumps({
            'sim_number': node.simulation_number,
            'type': 'Vote1',
            'data': data,
            'signature': send_signed(data,node.privatekey),
            'public_key': base64_representation
        })
    elif isinstance(obj, Vote2):
        data = {
            'sender': obj.sender,
            'QC_sender': obj.qc_sender
        }
        return json.dumps({
            'sim_number': node.simulation_number,
            'type': 'Vote2',
            'data': data,
            'signature': send_signed(data,node.privatekey),
            'public_key': base64_representation
        })
    
    elif isinstance(obj, Elect):
        data = {
            'sender': obj.sender,
        }
        return json.dumps({
            'sim_number': node.simulation_number,
            'type': 'Elect',
            'data': data,
            'signature': send_signed(data,node.privatekey),
            'public_key': base64_representation
        })
    
    elif isinstance(obj, Leader):
        data = {
            'sender': obj.sender,
            'id_leader': obj.id_leader
        }
        return json.dumps({
            'sim_number': node.simulation_number,
            'type': 'Leader',
            'data': data,
            'signature': send_signed(data,node.privatekey),
            'public_key': base64_representation
        })
    else :
        return json.dumps(obj.__dict__)
    
