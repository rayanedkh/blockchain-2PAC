import math
import time
import random
import inspect
import copy
import queue
import os
import json
import threading

#Imports de fichiers locaux
from sign import verify_signed
from data_struct import Block1,Vote1,Block2,Vote2,Elect,Leader
from tools import to_json
from com import Com


class Node:
    def __init__(self, id : int, host : str, port : int, peers : list, publickey, privatekey, delay: int, start_time, simulation_number: int,leader = 0,seed = 0):
        """initialisation de la classe Node"""
        
        # attributs propres au Node
        self.id = id    #de 1 à 4
        self.host = host    #localhost
        self.port = port    #port de communication du Node
        self.peers = peers  #liste de tuples comprenant les ports et le host des autres Nodes
        self.publickey = publickey  #clé publique du Node
        self.privatekey = privatekey    #clé privée du Node
        self.delay = delay         #entier pour savoir si le Node est delayed ou non, vaut 0 si il n'y a pas de delais et la valeur du délai sinon
        self.com=Com(self.id,self.port,self.peers,self.delay)   #classe de communication du Node
        self.success = False    #booléen pour savoir si le Node a réussi à commit un block
        self.stop_event = threading.Event()     #event pour arrêter le thread de gestion des messages lorsqu'un des Nodes a commit
        self.simulation_number = simulation_number #numéro de la simulation acutelle

        #Attributs pour stocker ses propres envoies de messages
        self.sentBlock2 = False     #booléen pour savoir si le Node a envoyé son Block2
        self.sentVote2 = []         #liste des Nodes à qui on a envoyé un Vote2
        self.sentCoinShare = False  #booléen pour savoir si le Node a envoyé son coinshare

        
        #attributs pour stocker les messages des autres Nodes
        self.blocks1 = {}       #dictionnaire des Block1 que l'on reçoit pour chaque autre Node
        self.qc1 = {self.id:[self.id]}      #dictionnaire qui stock pour chaque node la liste des Vote1 que l'on a reçu pour son Block1
        self.blocks2 = {}       #dictionnaire des Block2 que l'on reçoit pour chaque autre Node
        self.qc2 = {self.id:[self.id]}      #dictionnaire qui stock pour chaque node la liste des Vote2 que l'on a reçu pour son Block2
        self.elect = {}     #dictionnaire qui stock pour chaque node son message d'élection contenant sa coinshare
        self.leader = 0     #leader de la vue actuelle par défaut 0 (aucun leader élu)
        self.chain = []     #liste qui contient le block commit

        #attributs propres au réseau de Nodes
        if leader:
            self.qccoin = leader #qccoin choisi à l'avance
        else:
            random.seed(seed)
            self.qccoin = random.randint(1, 4) #qccoin choisi de manière déterministe mais change à chaque exécution, valeur commune à tous les nodes grâce à une seed d'aléatoire
        self.nodeNum = 4        #nombre de Nodes dans le réseau
        self.quorumNum = math.ceil(2 * self.nodeNum / 3.0)      #nombre de votes nécessaires pour obtenir un quorum certificate

        #logger
        self.starter_time = start_time

        #initialisation des données de logs
        self.datas_broadcastBlock1 = {'start':None,'end':None}
        self.datas_block1 = {1: None, 2: None, 3: None, 4: None}
        self.datas_broadcastVote1 = {1: {'start':None,'end':None}, 2: {'start':None,'end':None}, 3: {'start':None,'end':None}, 4: {'start':None,'end':None}}
        self.datas_vote1 = {"block sender 1": {1: None, 2: None, 3: None, 4: None}, "block sender 2": {1: None, 2: None, 3: None, 4: None}, "block sender 3": {1: None, 2: None, 3: None, 4: None}, "block sender 4": {1: None, 2: None, 3: None, 4: None}}
        self.datas_broadcastBlock2 = {'start':None,'end':None}
        self.datas_block2 = {1: None, 2: None, 3: None, 4: None}
        self.datas_broadcastVote2 = {1: {'start':None,'end':None}, 2: {'start':None,'end':None}, 3: {'start':None,'end':None}, 4: {'start':None,'end':None}}
        self.datas_vote2 = {"qc sender 1": {1: None, 2: None, 3: None, 4: None}, "qc sender 2": {1: None, 2: None, 3: None, 4: None}, "qc sender 3": {1: None, 2: None, 3: None, 4: None}, "qc sender 4": {1: None, 2: None, 3: None, 4: None}}
        self.datas_broadcastElect = {'start':None,'end':None}
        self.datas_elect = {1: None, 2: None, 3: None, 4: None}
        self.datas_broadcastLeader = {'start':None,'end':None}
        self.datas_leader = {1: None, 2: None, 3: None, 4: None}
        self.log_data={'Envoie Block1':{},'Receptions Block1':{},'Envoie Vote1':{},'Receptions Vote1':{},'Envoie Block2':{},'Receptions Block2':{},'Envoie Vote2':{},'Receptions Vote2':{},'Envoie Elect':{},'Receptions Elect':{},'Envoie Leader':{},'Receptions Leader':{},'Commit': None}

        #fichier log
        self.log_file_path = os.path.join('log', f'node_{self.id}.json')
        #on crée un dossier log si il n'existe pas
        if not os.path.exists('log'):
            os.makedirs('log')
        # on initialise les logs avec des json vides
        self.initialize_log_file()

   
    def handleMsgLoop(self):
        ''' Fonction pour gérer les messages reçus par le Node'''
        msgCh = self.com.recv
        while not self.stop_event.is_set():
            try:
                msgWithSig = msgCh.get(timeout=1)  # Utiliser un timeout pour éviter de bloquer indéfiniment
            except queue.Empty:
                continue
            msg_sim_number = msgWithSig['sim_number']
            if msg_sim_number != self.simulation_number: #si le socket n'est pas vide car il contient encore des messages de simulations précédentes, on ne les prend pas en compte
                continue
            msgAsserted = msgWithSig["data"]
            msg_type = msgWithSig["type"]
            msg_signature= msgWithSig["signature"]
            if not verify_signed(msg_signature): #on vérifie la signature du message
                continue
            if msg_type == 'Block1':
                block1=Block1(msgAsserted["sender"])
                self.handleBlock1Msg(block1)
            
            elif msg_type == 'Vote1':
                vote1=Vote1(msgAsserted["sender"],msgAsserted["Block_sender"])
                self.handleVote1Msg(vote1)
            
            elif msg_type == 'Block2':
                block2=Block2(msgAsserted["sender"],msgAsserted["qc"])
                self.handleBlock2Msg(block2)
            
            elif msg_type == 'Vote2':
                vote2=Vote2(msgAsserted["sender"],msgAsserted["QC_sender"])
                self.handleVote2Msg(vote2)
            
            elif msg_type == 'Elect':
                elect=Elect(msgAsserted["sender"])
                self.handleElectMsg(elect)
            elif msg_type == 'Leader':
                leader=Leader(msgAsserted["sender"],msgAsserted["id_leader"])
                self.handleLeaderMsg(leader)
            

#############       Handle Messages       #############
#########################################################
    def handleBlock1Msg(self, block1: Block1):
        ''' Fonction pour gérer les messages de type Block1 puis broadcast d'un message de type Vote1'''
        self.logger(block1)
        if block1.sender not in self.blocks1 and not self.leader: #on ne prend pas en compte les Block1 si on en a déjà reçu un du même Node ou après avoir élu un leader (et donc passé à la vue suivante)
            self.storeBlock1Msg(block1)
            if block1.sender not in self.qc1:
                self.qc1[block1.sender] = []
            self.qc1[block1.sender].append(self.id)
            self.broadcastVote1(block1.sender)      #La vérification du contenu du block avant de le voter est abstraite
            self.tryToCommit()
    

    def handleVote1Msg(self, vote1: Vote1):
        ''' Fonction pour gérer les messages de type Vote1 puis check du Quorum'''
        self.logger(vote1)
        if self.leader:    #on ne prend pas en compte les vote1 après avoir élu un leader (et donc passé à la vue suivante)
            return
        if vote1.block_sender not in self.qc1:
            self.qc1[vote1.block_sender] = []
        if vote1.sender not in self.qc1[vote1.block_sender]:
            self.storeVote1Msg(vote1)
            self.checkIfQuorum(vote1)
            self.tryToCommit()

    def handleBlock2Msg(self, block2: Block2):
        ''' Fonction pour gérer les messages de type Block2 puis broadcast d'un message de type Vote2'''
        self.logger(block2)
        if block2.sender not in self.blocks2 and not self.leader: #on ne prend pas en compte les Block2 si on en a déjà reçu un du même Node ou après avoir élu un leader (et donc passé à la vue suivante)
            self.storeBlock2Msg(block2)
            if block2.sender in self.qc1 and len(self.qc1[block2.sender]) >= self.quorumNum:
                self.sentVote2.append(block2.sender)
                if block2.sender not in self.qc2:
                    self.qc2[block2.sender] = []
                self.qc2[block2.sender].append(self.id)
                self.broadcastVote2(block2.sender)
                self.tryToCommit()

    def handleVote2Msg(self, vote2: Vote2):
        ''' Fonction pour gérer les messages de type Vote2 puis check du Quorum'''
        self.logger(vote2)
        if vote2.qc_sender not in self.qc2:
            self.qc2[vote2.qc_sender] = []
        if vote2.sender not in self.qc2[vote2.qc_sender]:
            self.storeVote2Msg(vote2)
            self.checkIfQuorum(vote2)
            self.tryToCommit()

    def handleElectMsg(self, elect: Elect):
        ''' Fonction pour gérer les messages de type Elect puis check du Quorum'''
        self.logger(elect)
        if not self.leader and elect.sender not in self.elect:
            self.storeElectMsg(elect)
            self.checkIfQuorum(elect)
            self.tryToCommit()
    
    def handleLeaderMsg(self, leader: Leader):
        ''' Fonction pour gérer les messages de type Leader puis tryToCommit'''
        t = time.time()-self.starter_time
        if t<1:
            print(t)
        self.logger(leader)
        if not self.leader:
            self.leader = leader.id_leader
            self.tryToCommit()
    


##############       Fonctions Store       ###############
#########################################################
    def storeBlock1Msg(self, block1: Block1):
        '''Fonction pour stocker les messages de type Block1'''
        self.blocks1[block1.sender] = block1

    def storeVote1Msg(self, vote1: Vote1):
        '''Fonction pour stocker les messages de type Vote1'''
        self.qc1[vote1.block_sender].append(vote1.sender)

    def storeBlock2Msg(self, block2: Block2):
        '''Fonction pour stocker les messages de type Block2'''
        self.blocks2[block2.sender] = block2
        if block2.sender not in self.qc1: #au cas où on reçoit un block2 étendant un block1 avant d'avoir reçu le moindre vote1 sur ce block1, on initialise le qc1 pour ce proposeur
            self.qc1[block2.sender] = []
        if block2.qc != None and len(self.qc1[block2.sender]) < self.quorumNum: #on suppose que la vérification de la validité de block2.qc a été faite
            self.qc1[block2.sender] = copy.deepcopy(block2.qc)

    def storeVote2Msg(self, vote2: Vote2):
        '''Fonction pour stocker les messages de type Vote2'''
        self.qc2[vote2.qc_sender].append(vote2.sender)

    def storeElectMsg(self, elect: Elect):
        '''Fonction pour stocker les messages de type Elect'''
        self.elect[elect.sender] = elect

##############       Check du Quorum Certificate      ##############
#########################################################
    def checkIfQuorum(self, msg):
        '''Fonction pour tester si on a un quorum certificate avec des Vote1, Vote2 ou Elect'''
        if type(msg) == Vote1:
            if len(self.qc1[msg.block_sender]) >= self.quorumNum:
                if msg.block_sender == self.id and not self.sentBlock2:
                    self.broadcastBlock2(self.qc1[self.id])
                if msg.block_sender in self.blocks2 and msg.block_sender not in self.sentVote2: 
                    self.sentVote2.append(msg.block_sender)
                    if msg.block_sender not in self.qc2:
                        self.qc2[msg.block_sender] = []
                    self.qc2[msg.block_sender].append(self.id)
                    self.broadcastVote2(msg.block_sender)
                        
        elif type(msg) == Vote2:
            if sum(len(qc2) >= self.quorumNum for qc2 in self.qc2.values()) >= self.quorumNum and not self.sentCoinShare:
                self.sentCoinShare = True
                self.elect[self.id] = Elect(self.id)
                self.broadcastElect()

        elif type(msg) == Elect:
            if len(self.elect) >= self.quorumNum:
                self.logger()
                self.leader = self.qccoin
                self.broadcastLeader(self.leader)


##################       Commit       ###################
#########################################################
    def tryToCommit(self):
        '''Fonction qui test si il est possbile de commit un Block1'''
        if self.leader: 
            if self.leader not in self.qc1 or self.leader not in self.qc2:
                return
            elif len(self.qc1[self.leader]) >= self.quorumNum and len(self.qc2[self.leader]) >= self.quorumNum and self.leader in self.blocks1:
                leader_block = self.blocks1[self.leader]
                self.chain.append(leader_block)
                self.success = True 
                

#################       Broadcast       #################
#########################################################

    def broadcastBlock1(self, block):
        '''Fonction pour envoyer un message de type Block1 à tous les autres Nodes'''
        self.logger('start')
        self.blocks1[self.id]= block #on stock son propre Block1 pour pouvoir le commit si on est élu comme leader
        self.datas_block1[self.id] = time.time()-self.starter_time
        self.com.broadcast_message(to_json(block, self))
        self.broadcastVote1(self.id)
        self.logger('end')
        
    def broadcastVote1(self, block_sender):
        '''Fonction pour envoyer un message de type Vote1 à tous les autres Nodes'''
        self.logger(block_sender,'start')
        self.datas_vote1[f"block sender {block_sender}"][self.id] = time.time()-self.starter_time
        message=Vote1(self.id,block_sender)
        self.com.broadcast_message(to_json(message, self))
        self.logger(block_sender,'end')
        
    def broadcastBlock2(self, qc=None):
        '''Fonction pour envoyer un message de type Block2 à tous les autres Nodes'''
        self.logger('start')
        message=Block2(self.id,qc)
        self.blocks2[self.id]= message
        self.sentBlock2 = True
        self.datas_block2[self.id] = time.time()-self.starter_time
        self.com.broadcast_message(to_json(message, self))
        self.logger('end')

    def broadcastVote2(self, qc_sender):
        '''Fonction pour envoyer un message de type Vote2 à tous les autres Nodes'''
        self.logger(qc_sender,'start')
        self.datas_vote2[f"qc sender {qc_sender}"][self.id] = time.time()-self.starter_time
        message=Vote2(self.id,qc_sender)
        self.com.broadcast_message(to_json(message, self))
        self.logger(qc_sender,'end')

    def broadcastElect(self):
        '''Fonction pour envoyer un message de type Elect à tous les autres Nodes'''
        self.logger('start')
        self.datas_elect[self.id] = time.time()-self.starter_time
        message=Elect(self.id)
        self.com.broadcast_message(to_json(message, self))
        self.logger('end')

    def broadcastLeader(self,leader):
        '''Fonction pour envoyer un message de type Leader à tous les autres Nodes'''
        self.logger('start')
        self.datas_leader[self.id] = time.time()-self.starter_time
        message=Leader(self.id,leader)
        self.com.broadcast_message(to_json(message, self))
        self.logger('end')



#################       Gestion des logs       #################
#########################################################

    def initialize_log_file(self):
        '''Fonction pour initialiser les fichiers de logs'''
        with open(self.log_file_path, 'w') as log_file:
            json.dump({}, log_file, indent=4)
    
    def write_log(self, log_data):
        '''Fonction pour écrire dans les fichiers de logs'''
        with open(self.log_file_path, 'w') as log_file:
            json.dump(log_data, log_file, indent=4)
    
    def logger(self,data=None,moment=None):
        '''Fonction pour mettre à jour les données de logs'''
        
        # on récupère la fonction dans laquelle on se trouve au moment où on appelle le logger
        current_frame = inspect.currentframe()
        caller_frame = current_frame.f_back
        function_name = caller_frame.f_code.co_name

        if function_name == "broadcastBlock1":
            delta = time.time()-self.starter_time
            self.datas_broadcastBlock1[data] = delta

        elif function_name == "handleBlock1Msg":
            delta = time.time()-self.starter_time
            self.datas_block1[data.sender] = delta

        elif function_name == "broadcastVote1":
            delta = time.time()-self.starter_time
            self.datas_broadcastVote1[data][moment] = delta
        
        elif function_name == "handleVote1Msg":
            delta = time.time()-self.starter_time
            self.datas_vote1[f"block sender {data.block_sender}"][data.sender] = delta

        elif function_name == "broadcastBlock2":
            delta = time.time()-self.starter_time
            self.datas_broadcastBlock2[data] = delta
        
        elif function_name == "handleBlock2Msg":
            delta = time.time()-self.starter_time
            self.datas_block2[data.sender] = delta

        elif function_name == "broadcastVote2":
            delta = time.time()-self.starter_time
            self.datas_broadcastVote2[data][moment] = delta

        elif function_name == "handleVote2Msg":
            delta = time.time()-self.starter_time
            self.datas_vote2[f"qc sender {data.qc_sender}"][data.sender] = delta

        elif function_name == "broadcastElect":
            delta = time.time()-self.starter_time
            self.datas_broadcastElect[data] = delta
        
        elif function_name == "handleElectMsg":
            delta = time.time()-self.starter_time
            self.datas_elect[data.sender] = delta

        elif function_name == "broadcastLeader":
            delta = time.time()-self.starter_time
            self.datas_broadcastLeader[data] = delta
                            
        elif function_name == "handleLeaderMsg":
            delta = time.time()-self.starter_time
            self.datas_leader[data.sender] = delta
    