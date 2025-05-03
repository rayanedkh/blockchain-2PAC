import threading
import time
import sys
import random

#Imports de fichiers locaux
from node import Node
from sign import generate_keypair
from data_struct import Block1

#on choisi 4 ports aléatoires différents entre 1000 et 9000 reservés pour les Nodes
list_ports = random.sample(range(1000, 9000), 4)
ports = {
    "node1": list_ports[0],
    "node2": list_ports[1],
    "node3": list_ports[2],
    "node4": list_ports[3],
}

#on crée les Block1 que chaque Node va envoyer
block1 = Block1(1)
block2 = Block1(2)
block3 = Block1(3)
block4 = Block1(4)

terminate_event = threading.Event() #on crée un event pour arrêter la boucle de vérification des commit


def setup_nodes(start_time,delay):
    '''Fonction pour instancier les Nodes'''
    seed = random.randint(1,1000) #on génère une seed random pour avoir un qccoin déterministe identique pour chaque Node mais qui change à chaque exécution
    random.seed(seed)
    print(f"Le leader désigné par le qccoin sera le Node n°{random.randint(1, 4)}")
    
    #on génère une paire de clés pour chaque Node et on les instancie, avec un retard pour le Node4
    privatekey4, publickey4 = generate_keypair()
    privatekey1, publickey1 = generate_keypair()
    privatekey2, publickey2 = generate_keypair()
    privatekey3, publickey3 = generate_keypair()
    node1 = Node(1,'localhost', ports["node1"], [('localhost', ports["node2"]), ('localhost', ports["node3"]), ('localhost', ports["node4"])], publickey1, privatekey1,0,start_time,1,seed=seed)
    node2 = Node(2,'localhost', ports["node2"], [('localhost', ports["node1"]), ('localhost', ports["node3"]), ('localhost', ports["node4"])], publickey2, privatekey2,0,start_time,1,seed=seed)
    node3 = Node(3,'localhost', ports["node3"], [('localhost', ports["node1"]), ('localhost', ports["node2"]), ('localhost', ports["node4"])], publickey3, privatekey3,0,start_time,1,seed=seed)
    node4 = Node(4,'localhost', ports["node4"], [('localhost', ports["node1"]), ('localhost', ports["node2"]), ('localhost', ports["node3"])], publickey4, privatekey4,delay,start_time,1,seed=seed)
    Nodes = [node1, node2, node3, node4]
    return Nodes

def write_result(node):
    '''Fonction pour écrire les logs à la fin de l'exécution'''
    node.log_data['Envoie Block1']=node.datas_broadcastBlock1
    node.log_data['Receptions Block1']=node.datas_block1
    node.log_data['Envoie Vote1']=node.datas_broadcastVote1
    node.log_data['Receptions Vote1']=node.datas_vote1
    node.log_data['Envoie Block2']=node.datas_broadcastBlock2
    node.log_data['Receptions Block2']=node.datas_block2
    node.log_data['Envoie Vote2']=node.datas_broadcastVote2
    node.log_data['Receptions Vote2']=node.datas_vote2
    node.log_data['Envoie Elect']=node.datas_broadcastElect
    node.log_data['Receptions Elect']=node.datas_elect
    node.log_data['Envoie Leader']=node.datas_broadcastLeader
    node.log_data['Receptions Leader']=node.datas_leader
    try:
        node.log_data['Commit']=f"Block du node : {node.chain[0].sender}"
    except:
        node.log_data['Commit']="Pas de block commit" 
    node.write_log(node.log_data)

def monitor_events(Nodes):
    '''Fonction pour vérifier en boucle si un block a été commit ou si aucun block ne peut être commit'''
    while not terminate_event.is_set():
        success_count = sum(node.success for node in Nodes)
        if success_count > 0:
            print(f'Succès, on a commit un block en {time.time()-start_time}s')
            print("Les logs des Nodes sont disponibles")
            for node in Nodes:
                node.stop_event.set()   #on ferme le thread de gestion des messages des Nodes avec stop_event
                write_result(node)      #on écrit les logs de chaque Node
            terminate_event.set()
        elif time.time()-start_time > 5*0.5+0.2: #on sait qu'on a pas commit au bout de 5 delta mais on rajoute une marge dûe au temps d'envoie des messages (non nul après avoir attendu delta)
            print(f'Echec, on a commit aucun block en {time.time()-start_time}s')
            print("Les logs des Nodes sont disponibles")
            for node in Nodes:
                node.stop_event.set()
                write_result(node)
            terminate_event.set()
        time.sleep(0.1)  #on attend un certain temps pour ne pas surcharger le processeur mais plus on prend petit plus on est précis sur le temps de commit
    

if __name__ == "__main__":
    start_time = time.time()

    delay = float(sys.argv[1]) #délai de retard du Node4, toutes les communications sur le réseau prennent 0.5s (valeur arbitraire de delta_fast grande devant les temps de communication réels qui permet de négliger leur aléat)
    #calcul de la valeur du délai : les communications du Node4 prennent 0.5s + delay puis les réponses des autres Nodes prennet 0.5s. La communication totale prend donc 2*0.5s + delay
    #calcul de delta : delta (comme défini dans le papier 2PAC) vaut donc (2*0.5 + delay)/2 = 0.5 + delay/2 (on considère que les messages partant du Node4 et vers le Node4 prennent le même temps delta_fast)
    #différents cas : si 0 <= delay <= 0.5 (delta_fast) alors delta_fast <= delta <= delta_fast*3/2 (GradedDAG doit commit) si 0.5 < delay <= 1 (2*delta_fast) alors delta_fast*3/2 < delta <= delta_fast*2 (GradedDAG ne doit pas commit) si 1 < delay alors 2*delta_fast < delta (GradedDAG ne doit pas commit)
     
    #on instancie les Nodes avec le délai choisi pour le Node4 puis on lance leur module de communication
    Nodes = setup_nodes(start_time,delay)
    for node in Nodes:
        node.com.start()


    #on lance des threads pour que chaque Node gère les messages reçus
    threads = [
        threading.Thread(target=Nodes[0].handleMsgLoop),
        threading.Thread(target=Nodes[1].handleMsgLoop),
        threading.Thread(target=Nodes[2].handleMsgLoop),
        threading.Thread(target=Nodes[3].handleMsgLoop),
    ]

    for thread in threads:
        thread.start()

    _2PAC_pire_cas = False #variable pour choisir si on se place dans le pire cas de 2PAC et donc si chaque node attent d'avoir crée un qc sur son propre Block1 avant de créer le Block2 qui l'étend

    #on envoie les Blocks de chaque Node
    Nodes[0].broadcastBlock1(block1)
    Nodes[1].broadcastBlock1(block2)
    Nodes[2].broadcastBlock1(block3)
    Nodes[3].broadcastBlock1(block4)
    if not _2PAC_pire_cas:
        Nodes[0].broadcastBlock2()
        Nodes[1].broadcastBlock2()
        Nodes[2].broadcastBlock2()
        Nodes[3].broadcastBlock2()


    #on lance un thread qui vérifie en boucle si un block a été commit ou si aucun block ne peut plus être commit
    monitor_thread = threading.Thread(target=monitor_events, args=(Nodes,))
    monitor_thread.start()

    #on attend que tous les threads soient terminés
    for thread in threads:
        thread.join()
    monitor_thread.join()

    #on attent 1s pour être sûrs que les threads de gestion des messages et de vérification du commit soient terminées puis on arrête les com (on ferme les socket et les threads)
    time.sleep(1)
    for node in Nodes:
        node.com.stop()