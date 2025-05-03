import socket
import threading
import queue
import json
import time


class Com:
    """structure Com qui implémente les fonctions de communication entre les noeuds du réseau"""
    def __init__(self,id = None, port = None, peers = None, delay = 0):
        """initialisation de la classe Com"""
        self.id = id        #id du noeud
        self.host = 'localhost'     #adresse du noeud
        self.port = port        #port du noeud
        self.peers = peers      #pairs du noeud (adresses des noeuds avec qui il peut communiquer)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       #socket du noeud (utilisé pour la communication)
        self.sock.bind((self.host, self.port))      #liaison du socket à l'adresse et au port du noeud
        self.threads = []       #liste des threads du noeud
        self.recv = queue.Queue()       #file d'attente des messages reçus par le noeud
        self.delay = delay      #délai d'envoi des messages (entier)
        self.stop_event = threading.Event() #évènement pour arrêter les boucles des threads
        self.client_socks = [] #liste pour stocker les socket pour établir connexions à la demande d'un autre Node
        self.lock = threading.Lock() #cadenas pour empêcher un accès concurrentiel à certaines variables entre les différents threads

    def start(self):
        """fonction de démarrage du noeud"""
        self.start_server()
        self.connect_to_peers()
        return self

    def start_server(self):
        """"fonction de démarrage du serveur du noeud"""
        server_thread = threading.Thread(target=self.listen_for_connections)
        server_thread.start()
        self.threads.append(server_thread)

    def listen_for_connections(self):
        """fonction d'écoute des connexions entrantes"""
        self.sock.listen(20)     # le socket peut gérer jusqu'à 20 connexions en attente simultanément avant de refuser ou de mettre en attente les connexions supplémentaires
        while not self.stop_event.is_set():
            try:
                client_sock, _ = self.sock.accept()
                client_sock.settimeout(1) #on met un timeout pour éviter d'attendre sans fin
                with self.lock:
                    self.client_socks.append(client_sock)
                client_thread = threading.Thread(target=self.handle_client, args=(client_sock,)) #on crée un thread pour gérer les messages avec l'autre Node après avoir accepté la connexion
                client_thread.start()
                self.threads.append(client_thread)
            except socket.timeout:
                continue
            except Exception as e:
                if not self.stop_event.is_set():
                    print(f"Exception dans listen_for_connections: {e}")
                break

    def connect_to_peers(self):
        """fonction de connexion aux pairs du noeud"""
        for peer in self.peers:     #pour chaque pair du noeud on crée un thread pour se connecter à ce pair
            peer_thread = threading.Thread(target=self.connect_to_peer, args=(peer,))
            peer_thread.start()
            self.threads.append(peer_thread)

    def connect_to_peer(self, peer):
        """fonction de connexion à un pair du noeud"""
        peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       
        while not self.stop_event.is_set():
            try:
                peer_sock.connect(peer)
                with self.lock:
                    self.client_socks.append(peer_sock)
                self.handle_client(peer_sock)
                break
            except ConnectionRefusedError:
                time.sleep(1)  #On attend avant de retenter de se connecter
            except Exception as e:
                if not self.stop_event.is_set():
                    print(f"Exception dans connect_to_peer: {e}")
                break

    def handle_client(self, client_sock):
        """fonction de gestion des clients connectés au noeud"""
        try:
            while not self.stop_event.is_set():
                try:
                    data = client_sock.recv(1024) #on récupère les données dans le socket
                    if not data:
                        break
                    message = data.decode('utf-8')
                    message = json.loads(message)
                    self.recv.put(message) #on ajoute le message à la queue
                except socket.timeout:
                    continue
                except Exception as e:
                    if not self.stop_event.is_set():
                        print(f"Erreur dans handle_client: {e}")
                    break
        finally:
            self.close_socket(client_sock)


    def broadcast_message(self, message):
        """fonction d'envoi de message à tous les pairs du noeud"""
        for peer in self.peers:
            threading.Thread(target=self.delayed_send, args=(message, peer)).start() #on crée un thread différent pour chaque envoie de message à des Nodes différents

    def delayed_send(self, message, peer):
        '''fonction pour attendre un certain délai avant d'envoyer réellement le message'''
        time.sleep(0.5 + self.delay)
        self.send_message(message, peer)

    def send_message(self, message, peer):
        """fonction d'envoi de message à un pair du noeud"""
        if self.stop_event.is_set():
            return
        peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            peer_sock.connect(peer)
            peer_sock.sendall(message.encode('utf-8'))
            peer_sock.close()
        except ConnectionRefusedError:
            if not self.stop_event.is_set():
                print(f"Impossible d'envoyer un message au pair : {peer}")
        except Exception as e:
            if not self.stop_event.is_set():
                print(f"Exception dans send_message: {e}")

    def close_socket(self, sock):
        """fonction de fermeture sécurisée d'un socket"""
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except Exception as e:
                if not self.stop_event.is_set():
                    print(f"Exception l'éteignage du socket client: {e}")
            try:
                sock.close()
            except Exception as e:
                if not self.stop_event.is_set():
                    print(f"Exception la fermeture du socket client: {e}")

    def is_socket_connected(self,sock):
        """fonction pour verifier si un socket est toujours connecté"""
        try:
            sock.getpeername()
        except socket.error:
            return False
        return True

    def stop(self):
        """fonction d'arrêt du noeud"""
        self.stop_event.set()
        with self.lock: #on ferme tous les sockets de connexion avec les autres Nodes
            for sock in self.client_socks:
                self.close_socket(sock)
            self.client_socks.clear()
        for thread in self.threads: #on attent la fin de tous les threads encore actifs
            if thread.is_alive():
                thread.join(timeout=0.5)

        #on ferme notre propre socket
        try:
            if self.sock and self.is_socket_connected(self.sock):
                self.sock.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print(f"Exception pendant l'éteignage de notre propre socket: {e}")
        try:
            if self.sock:
                self.sock.close()
        except Exception as e:
            print(f"Exception pendant la fermeture de notre propre socket: {e}")
