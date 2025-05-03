import json
from nacl import signing

def generate_keypair():
    '''Fonction pour générer une clé privée et une clé publique'''
    private_key = signing.SigningKey.generate()
    public_key = private_key.verify_key
    return private_key, public_key


def send_signed(data,private_key):
    '''Fonction pour signer un message'''

    data_json = json.dumps(data).encode('utf-8')

    signing_key = signing.SigningKey(private_key.encode())
    signed = signing_key.sign(data_json)

    message_hex = signed.message.hex()
    signature_hex = signed.signature.hex()
    public_key_hex = signing_key.verify_key.encode().hex()

    signed_message_dict = {
        'message': message_hex,
        'signature': signature_hex,
        'public_key': public_key_hex
    }
    return json.dumps(signed_message_dict)

def verify_signed(signed_message_json):
    '''Fonction pour vérifier la signature d'un message'''
    signed_message_dict = json.loads(signed_message_json)
    public_key_hex = signed_message_dict['public_key']

    try:
        public_key_bytes = bytes.fromhex(public_key_hex)
        verify_key = signing.VerifyKey(public_key_bytes)
        
        signature_bytes = bytes.fromhex(signed_message_dict['signature'])
        message_bytes = bytes.fromhex(signed_message_dict['message'])
            
        signed_message_combined = signature_bytes + message_bytes
        
        verify_key.verify(signed_message_combined)
        return True
    except Exception as e:
        print("La verification a échouée:", e)
        return False