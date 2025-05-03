import math
import time
import random
import inspect
import queue
import os
import json
import threading

#Imports de fichiers locaux
from sign import verify_signed
from data_struct import Block,Echo,Ready,Elect,Leader
from tools import to_json
from com import Com



class Node:
    def __init__(self, id : int, host : str, port : int, peers : list, publickey, privatekey, delay: int, start_time, simulation_number: int,leader = 0,seed = 0):
        """initialisation de la classe Node"""

        #Attributs propres au Node
        self.id = id                                            #de 1 à 4
        self.host = host                                        #localhost
        self.port = port                                        #port de communication du Node
        self.peers = peers                                      #liste de tuples comprenant les ports et le host des autres Nodes
        self.publickey = publickey                              #clé publique du Node
        self.privatekey = privatekey                            #clé privée du Node
        self.delay = delay                                      #entier pour savoir si le Node est delayed ou non, vaut 0 si il n'y a pas de delais et la valeur du délai sinon
        self.com=Com(self.id,self.port,self.peers,self.delay)   #classe de communication du Node
        self.success = False                                    #booléen pour savoir si le Node a réussi à commit un block
        self.stop_event = threading.Event()                     #event pour arrêter le thread de gestion des messages lorsqu'un des Nodes a commit
        self.simulation_number = simulation_number              #numéro de la simulation acutelle

        #Attributs pour stocker ses propres envoies de messages
        self.sentReady = []                                     #liste des Nodes à qui on a envoyé un ready
        self.sentCoinShare = False                              #booléen pour savoir si le Node a envoyé son coinshare

        
        #Attributs pour stocker les messages des autres Nodes
        self.blocks = {}                                        #dictionnaire des blocks que l'on reçoit pour chaque autre Node
        self.grade1 = []                                        #liste des id de Nodes dont le Block est grade1 (qui a un qc de echo)
        self.qc1 = {self.id:[self.id]}                          #dictionnaire qui stock pour chaque node la liste des echo que l'on a reçu pour son block
        self.qc2 = {self.id:[self.id]}                          #dictionnaire qui stock pour chaque node la liste des ready que l'on a reçu pour son block
        self.elect = {}                                         #dictionnaire qui stock pour chaque node son message d'élection contenant sa coinshare
        self.leader = 0                                         #leader de la vue actuelle par défaut 0 (aucun leader élu)
        self.chain = []                                         #liste qui contient le block commit

        #Attributs propres au réseau de Nodes
        if leader:
            self.qccoin = leader #qccoin choisi à l'avance
        else:
            random.seed(seed)
            self.qccoin = random.randint(1, 4) #qccoin choisi de manière déterministe mais change à chaque exécution, valeur commune à tous les nodes grâce à une seed d'aléatoire
        self.nodeNum = 4                                        #nombre de Nodes dans le réseau
        self.quorumNum = math.ceil(2 * self.nodeNum / 3.0)      #nombre de votes nécessaires pour obtenir un quorum certificate
        self.thirdNum = math.ceil(self.nodeNum / 3.0)           #nombre de votes nécessaires pour avoir f+1 votants (parmis 3f+1)

        #Logger
        self.starter_time = start_time                          #temps de départ (le même pour tous les Nodes)
        
        #initialisation des données de logs
        self.datas_broadcastBlock = {'start':None,'end':None}
        self.datas_block = {1: None, 2: None, 3: None, 4: None}
        self.datas_broadcastEcho = {1: {'start':None,'end':None}, 2: {'start':None,'end':None}, 3: {'start':None,'end':None}, 4: {'start':None,'end':None}}
        self.datas_echo = {"block sender 1": {1: None, 2: None, 3: None, 4: None}, "block sender 2": {1: None, 2: None, 3: None, 4: None}, "block sender 3": {1: None, 2: None, 3: None, 4: None}, "block sender 4": {1: None, 2: None, 3: None, 4: None}}
        self.datas_broadcastReady = {1: {'start':None,'end':None}, 2: {'start':None,'end':None}, 3: {'start':None,'end':None}, 4: {'start':None,'end':None}}
        self.datas_ready = {"block sender 1": {1: None, 2: None, 3: None, 4: None}, "block sender 2": {1: None, 2: None, 3: None, 4: None}, "block sender 3": {1: None, 2: None, 3: None, 4: None}, "block sender 4": {1: None, 2: None, 3: None, 4: None}}
        self.datas_broadcastElect = {'start':None,'end':None}
        self.datas_elect = {1: None, 2: None, 3: None, 4: None}
        self.datas_broadcastLeader = {'start':None,'end':None}
        self.datas_leader = {1: None, 2: None, 3: None, 4: None}
        self.log_data={'Envoie Block':{},'Receptions Block':{},'Envoie Echo':{},'Receptions Echo':{},'Envoie Ready':{},'Receptions Ready':{},'Envoie Elect':{},'Receptions Elect':{},'Envoie Leader':{},'Receptions Leader':{},'Commit': None}

        #Fichier log
        self.log_file_path = os.path.join('log', f'node_{self.id}.json')
        #on crée un dossier log si il n'existe pas
        if not os.path.exists('log'):                           #on crée le dossier log s'il n'existe pas
            os.makedirs('log')
        # on initialise les logs avec des json vides
        self.initialize_log_file()                              # on initialise les logs avec des json vides

   
    def handleMsgLoop(self):
        ''' Fonction pour gérer les messages reçus par le Node'''
        self.logger()
        msgCh = self.com.recv
        while not self.stop_event.is_set():
            try:
                msgWithSig = msgCh.get(timeout=1)               # Utiliser un timeout pour éviter de bloquer indéfiniment
            except queue.Empty:
                continue
            msg_sim_number = msgWithSig['sim_number']
            if msg_sim_number != self.simulation_number: #si le socket n'est pas vide car il contient encore des messages de simulations précédentes, on ne les prend pas en compte
                continue
            msgAsserted = msgWithSig["data"]
            msg_type = msgWithSig["type"]
            msg_signature= msgWithSig["signature"]
            if not verify_signed(msg_signature):                #on vérifie la signature du message
                continue
            if msg_type == 'Block':
                block=Block(msgAsserted["sender"])
                self.handleBlockMsg(block)
            
            elif msg_type == 'Echo':
                echo=Echo(msgAsserted["sender"],msgAsserted["Block_sender"])
                self.handleEchoMsg(echo)
            
            elif msg_type == 'Ready':
                ready=Ready(msgAsserted["sender"],msgAsserted["Block_sender"])
                self.handleReadyMsg(ready)
            
            elif msg_type == 'Elect':
                elect=Elect(msgAsserted["sender"])
                self.handleElectMsg(elect)

            elif msg_type == 'Leader':
                leader=Leader(msgAsserted["sender"],msgAsserted["id_leader"])
                self.handleLeaderMsg(leader)
            

#############       Handle Messages       #############
#########################################################
    def handleBlockMsg(self, block: Block):
        ''' Fonction pour gérer les messages de type Block puis broadcast d'un message de type Echo'''
        self.logger(block)
        if block.sender not in self.blocks:
            if self.sentCoinShare and block.sender not in self.grade1:      #Les nouveaux blocks qui ne sont pas de grade 1 ne sont pas pris un compte après avoir envoyé sa coinshare
                return
            self.storeBlockMsg(block)
            if block.sender not in self.qc1:
                self.qc1[block.sender] = []
            self.qc1[block.sender].append(self.id)
            self.broadcastEcho(block.sender)   #La vérification du contenu du block avant de le voter est abstraite
            self.tryToCommit()
    

    def handleEchoMsg(self, echo: Echo):
        ''' Fonction pour gérer les messages de type Echo puis check du Quorum'''
        self.logger(echo)
        if self.sentCoinShare and echo.block_sender not in self.grade1:             #Les echo pour un block qui n'est pas grade 1 (non reçeption d'un qc de echo) ne sont pas pris en compte après avoir envoyé son coinshare
            return
        if echo.block_sender not in self.qc1:
            self.qc1[echo.block_sender] = []
        if echo.sender not in self.qc1[echo.block_sender]:
            self.storeEchoMsg(echo)
            self.checkIfQuorum(echo)


    def handleReadyMsg(self, ready: Ready):
        ''' Fonction pour gérer les messages de type Ready puis check du Quorum'''
        self.logger(ready)
        if self.sentCoinShare and ready.block_sender not in self.grade1:            #on ne prend les ready pour un block qui n'est pas grade 1 (dont on a pas reçu de qc de echo) après avoir envoyé son coinshare
            return
        if ready.block_sender not in self.qc2:
            self.qc2[ready.block_sender] = []
        if ready.sender not in self.qc2[ready.block_sender]:
            self.storeReadyMsg(ready)
            self.checkIfQuorum(ready)
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
        self.logger(leader)
        if not self.leader:
            self.leader = leader.id_leader
            self.tryToCommit()
    


##############       Fonctions Store       ###############
#########################################################
    def storeBlockMsg(self, block: Block):
        '''Fonction pour stocker les messages de type Block'''
        self.logger()
        self.blocks[block.sender] = block

    def storeEchoMsg(self, echo: Echo):
        '''Fonction pour stocker les messages de type Echo'''
        self.logger()
        self.qc1[echo.block_sender].append(echo.sender)

    def storeReadyMsg(self, ready: Ready):
        '''Fonction pour stocker les messages de type Ready'''
        self.logger()
        self.qc2[ready.block_sender].append(ready.sender)

    def storeElectMsg(self, elect: Elect):
        '''Fonction pour stocker les messages de type Elect'''
        self.logger()
        self.elect[elect.sender] = elect

##############       Check du Quorum Certificate      ##############
#########################################################
    def checkIfQuorum(self, msg):
        '''Fonction pour tester si on a un quorum certificate avec des Echo, Ready ou Elect'''
        if type(msg) == Echo:
            if len(self.qc1[msg.block_sender]) >= self.quorumNum and msg.block_sender not in self.sentReady:
                self.sentReady.append(msg.block_sender)
                self.grade1.append(msg.block_sender)
                if msg.block_sender not in self.qc2:
                    self.qc2[msg.block_sender] = []
                self.qc2[msg.block_sender].append(self.id)
                self.broadcastReady(msg.block_sender)
                        
        elif type(msg) == Ready:
            if len(self.qc2[msg.block_sender]) >= self.thirdNum and msg.block_sender not in self.sentReady:
                self.sentReady.append(msg.block_sender)
                self.grade1.append(msg.block_sender)
                if msg.block_sender not in self.qc2:
                    self.qc2[msg.block_sender] = []
                self.qc2[msg.block_sender].append(self.id)
                self.broadcastReady(msg.block_sender)
            if sum(len(qc2) >= self.quorumNum for qc2 in self.qc2.values()) >= self.quorumNum and not self.sentCoinShare:
                self.sentCoinShare = True
                self.elect[self.id] = Elect(self.id)
                self.broadcastElect()

        elif type(msg) == Elect:
            if len(self.elect) >= self.quorumNum:
                self.leader = self.qccoin
                self.broadcastLeader(self.leader)


##################       Commit       ###################
#########################################################
    def tryToCommit(self):
        '''Fonction qui test si il est possbile de commit un block'''
        if self.leader: 
            if self.leader not in self.qc2:
                return
            elif len(self.qc2[self.leader]) >= self.quorumNum and self.leader in self.blocks: #on vérifie uniquement que le block du leader est grade2 car il est a fortiori grade1
                leader_block = self.blocks[self.leader]
                self.chain.append(leader_block)
                self.success = True 
        

#################       Broadcast       #################
#########################################################

    def broadcastBlock(self, block):
        '''Fonction pour envoyer un message de type Block à tous les autres Nodes'''
        self.logger('start')
        self.blocks[self.id]= block #on stock son propre Block pour pouvoir le commit si on est élu comme leader
        self.datas_block[self.id] = time.time()-self.starter_time
        self.com.broadcast_message(to_json(block, self))
        self.broadcastEcho(self.id)
        self.logger('end')
        
    def broadcastEcho(self, block_sender):
        '''Fonction pour envoyer un message de type Echo à tous les autres Nodes'''
        self.logger(block_sender,'start')
        self.datas_echo[f"block sender {block_sender}"][self.id] = time.time()-self.starter_time
        message=Echo(self.id,block_sender)
        self.com.broadcast_message(to_json(message, self))
        self.logger(block_sender,'end')

    def broadcastReady(self, block_sender):
        '''Fonction pour envoyer un message de type Ready à tous les autres Nodes'''
        self.logger(block_sender,'start')
        self.datas_ready[f"block sender {block_sender}"][self.id] = time.time()-self.starter_time
        message=Ready(self.id,block_sender)
        self.com.broadcast_message(to_json(message, self))
        self.logger(block_sender,'end')

    def broadcastElect(self):
        '''Fonction pour envoyer un message de type Elect à tous les autres Nodes'''
        self.logger('start')
        self.datas_elect[self.id] = time.time()-self.starter_time
        message=Elect(self.id)
        self.com.broadcast_message(to_json(message, self))
        self.logger('end')

    def broadcastLeader(self, leader):
        '''Fonction pour envoyer un message de type Leader à tous les autres Nodes'''
        self.logger('start')
        self.datas_leader[self.id] = time.time()-self.starter_time
        message=Leader(self.id,leader)
        self.com.broadcast_message(to_json(message, self))
        self.logger('end')



##############       Gestion des logs       #############
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

        #On récupère le nom de la fonction dans laquelle on se trouvait lorsque l'on a appelé logger
        current_frame = inspect.currentframe()
        caller_frame = current_frame.f_back
        function_name = caller_frame.f_code.co_name

        if function_name == "broadcastBlock":
            delta = time.time()-self.starter_time
            self.datas_broadcastBlock[data] = delta

        elif function_name == "handleBlockMsg":
            delta = time.time()-self.starter_time
            self.datas_block[data.sender] = delta

        elif function_name == "broadcastEcho":
            delta = time.time()-self.starter_time
            self.datas_broadcastEcho[data][moment] = delta
        
        elif function_name == "handleEchoMsg":
            delta = time.time()-self.starter_time
            self.datas_echo[f"block sender {data.block_sender}"][data.sender] = delta

        elif function_name == "broadcastReady":
            delta = time.time()-self.starter_time
            self.datas_broadcastReady[data][moment] = delta

        elif function_name == "handleReadyMsg":
            delta = time.time()-self.starter_time
            self.datas_ready[f"block sender {data.block_sender}"][data.sender] = delta

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
    