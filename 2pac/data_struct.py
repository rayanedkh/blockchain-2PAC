import json

#############       Création des objets pour chaque type de messages entre les Nodes       #############
########################################################################################################

class Block:
    """Classe abstraite d'un bloc qu'un noeud peut envoyer"""
    def __init__(self, sender):
        """initialisation de la classe Block"""
        self.sender = sender 
        #on abstrait les tx en supposant que la pool est inépuisable et qu'on peut toujours remplir la data du block avec des tx


    def to_json(self):
        '''fonction pour mettre un Block au format json'''
        return json.dumps({
            'sender': self.sender
        })

class Block1(Block):
    """Classe d'un Block de hauteur 1"""
    def __init__(self, sender):
        """initialisation de la classe Block2"""
        super().__init__(sender)

    def to_json(self):
        '''fonction pour mettre un Block1 au format json'''
        return json.dumps({
            'sender': self.sender
        })


class Block2(Block):
    """Classe d'un Block de hauteur 2"""
    def __init__(self, sender, qc):
        """initialisation de la classe Block2"""
        super().__init__(sender)
        self.qc = qc #qc peut valoir None, comme on est que sur une seule view on considère toujours que le Block2 d'un replica extend le Block1 de ce même replica
    
    def to_json(self):
        '''fonction pour mettre un Block3 au format json'''
        return json.dumps({
            'sender': self.sender,
            'QC': self.qc
        })

class Vote:
    """Classe abstraite d'un vote qu'un noeud peut envoyer"""
    def __init__(self, vote_sender):
        """initialisation de la classe Vote"""
        self.sender = vote_sender

    def to_json(self):
        '''fonction pour mettre un Vote au format json'''
        return json.dumps({
            'sender': self.sender
        })


class Vote1(Vote):
    """Classe d'un vote de type 1"""
    def __init__(self, vote_sender, block_sender):
        """initialisation de la classe Vote1"""
        super().__init__(vote_sender)
        self.block_sender = block_sender

    def to_json(self):
        '''fonction pour mettre un Vote1 au format json'''
        return json.dumps({
            'sender': self.sender,
            'Block_sender': self.block_sender
        })

class Vote2(Vote):
    """Classe d'un vote de type 2"""
    def __init__(self, vote_sender, qc_sender):
        """initialisation de la classe Vote2"""
        super().__init__(vote_sender)
        self.qc_sender = qc_sender

    def to_json(self):
        '''fonction pour mettre un Vote2 au format json'''
        return json.dumps({
            'sender': self.sender,
            'qc_sender': self.qc_sender
        })
    
class Elect:
    """Classe abstraite d'un message d'élection qu'un noeud peut envoyer"""
    def __init__(self, sender):
        """initialisation de la classe Elect"""
        self.sender = sender
        #on abstrait data = qcCoinshare

class Leader:
    """Classe abstraite d'un message de type Leader qu'un noeud peut envoyer"""
    def __init__(self, sender,id_leader):
        """initialisation de la classe Leader"""
        self.sender = sender
        self.id_leader = id_leader
        #on pourrait rajouter block1 qc1 et qc2 du leader si on les a pour accélerer les commit