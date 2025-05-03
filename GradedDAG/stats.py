import threading
import time
import random
import numpy as np
import csv
import queue
import os
import shutil

# Imports de fichiers locaux
from node import Node
from sign import generate_keypair
from data_struct import Block


#on choisi 4 ports aléatoires différents entre 1000 et 9000 reservés pour les Nodes
list_ports = random.sample(range(1000, 9000), 4)
ports = {
    "node1": list_ports[0],
    "node2": list_ports[1],
    "node3": list_ports[2],
    "node4": list_ports[3],
}

#on crée les blocks que chaque Node va envoyer
block1 = Block(1)
block2 = Block(2)
block3 = Block(3)
block4 = Block(4)


def setup_nodes(start_time, delay, leader, simulation_number):
    '''Fonction pour instancier les Nodes'''
    
    #on génère une paire de clés pour chaque Node et on les instancie, avec un retard pour le Node4
    privatekey4, publickey4 = generate_keypair()
    privatekey1, publickey1 = generate_keypair()
    privatekey2, publickey2 = generate_keypair()
    privatekey3, publickey3 = generate_keypair()
    node1 = Node(1, 'localhost', ports["node1"], [('localhost', ports["node2"]), ('localhost', ports["node3"]), ('localhost', ports["node4"])], publickey1, privatekey1, 0, start_time, simulation_number,leader=leader)
    node2 = Node(2, 'localhost', ports["node2"], [('localhost', ports["node1"]), ('localhost', ports["node3"]), ('localhost', ports["node4"])], publickey2, privatekey2, 0, start_time, simulation_number,leader=leader)
    node3 = Node(3, 'localhost', ports["node3"], [('localhost', ports["node1"]), ('localhost', ports["node2"]), ('localhost', ports["node4"])], publickey3, privatekey3, 0, start_time, simulation_number,leader=leader)
    node4 = Node(4, 'localhost', ports["node4"], [('localhost', ports["node1"]), ('localhost', ports["node2"]), ('localhost', ports["node3"])], publickey4, privatekey4, delay, start_time, simulation_number,leader=leader)
    Nodes = [node1, node2, node3, node4]
    return Nodes


def monitor_events(Nodes, start_time, result_queue):
    '''Fonction pour vérifier en boucle si un block a été commit ou si aucun block ne peut être commit'''
    while True:
        success_count = sum(node.success for node in Nodes)
        if success_count > 0:
            commit_time = time.time() - start_time
            for node in Nodes:
                node.stop_event.set() #on ferme le thread de gestion des messages des Nodes avec stop_event
            result_queue.put((True, commit_time)) #on ajoute les resultats dans une queue pour y accéder entre les différents threads en temps direct
            return
        elif time.time() - start_time > 5 * 0.5 + 0.2:  # on sait qu'on a pas commit au bout de 5 delta mais on rajoute une marge dûe au temps d'envoie des messages (non nul après avoir attendu delta)
            for node in Nodes:
                node.stop_event.set()
            result_queue.put((False, 0))
            return
        time.sleep(0.1)  # on attend un certain temps pour ne pas surcharger le processeur mais plus on prend petit plus on est précis sur le temps de commit


def run_simulation(delay,leader,simulation_number):
    '''fonction pour lancer la simulation d'une vue'''
    start_time = time.time()
    result_queue = queue.Queue() #on crée une queue pour ajouter et retirer les resultats du commit de manière dynamique entre les threads
    
    #on instancie les Nodes avec le délai choisi pour le Node4 puis on lance leur module de communication
    Nodes = setup_nodes(start_time, delay,leader,simulation_number)
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

    #on envoie les Blocks de chaque Node
    Nodes[0].broadcastBlock(block1)
    Nodes[1].broadcastBlock(block2)
    Nodes[2].broadcastBlock(block3)
    Nodes[3].broadcastBlock(block4)

    #on lance un thread qui vérifie en boucle si un block a été commit ou si aucun block ne peut plus être commit
    monitor_thread = threading.Thread(target=monitor_events, args=(Nodes, start_time, result_queue))
    monitor_thread.start()

    #on attend que tous les threads soient terminés
    for thread in threads:
        thread.join()
    monitor_thread.join()

    #on attent 1s pour être sûrs que les threads de gestion des messages et de vérification du commit soient terminées puis on arrête les com (on ferme les socket et les threads)
    time.sleep(1)
    for node in Nodes:
        node.com.stop()
    
    #on récupère les résultats dans la queue
    commit, commit_time = result_queue.get()

    return commit, commit_time


def main():
    '''fonction principale'''
    print('début de la simulation')
    
    #on choisit le nombre d'itérations que l'on souhaite simuler
    num_simulations = 1000

    #pour la simulation nous avons choisi une distribution du retard du Node4 normale centrée en 0 avec un écart-type de 0.7s (en valeur absolue pour avoir un retard toujours positif)
    #ainsi la probabilité que le retard soit entre 0s et 0.5s (delta_fast) est d'environs 53%
    #la probabilité que le retard soit entre 0.5s (delta_fast) et 1s (2*delta_fast) est d'envrions 32%
    #la probabilité que le retard soit supérieur à 1s (2*delta_fast) est d'envrions 15%
    np.random.seed(0)
    delays = np.abs(np.random.normal(0, 0.7, num_simulations))

    leaders = [(i % 4) + 1 for i in range(num_simulations)]

    results = []

    for simulation_number, (delay, leader) in enumerate(zip(delays, leaders), 1):
        commit, commit_time = run_simulation(delay,leader,simulation_number)
        results.append([simulation_number, delay, leader, commit, commit_time])
        if simulation_number%(num_simulations//10)==0: #on affiche la progression de la simulation tous les multiples de 10%
            print(f'{int(simulation_number*100/num_simulations)}%')
        time.sleep(0.5) #on ajoute un délai pour s'assurer de la libération des ressources

    #On écrit les résultats dans un fichier csv
    with open('simulation_results.csv', 'w', newline='') as csvfile:
        fieldnames = ['simulation_number','delay', 'leader', 'commit', 'commit_time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow({
                'simulation_number': result[0],
                'delay': round(result[1],2),
                'leader': result[2],
                'commit': result[3],
                'commit_time': round(result[4],2)
            })

    #On calcule les statistiques de la simulation
    total_commits = sum(1 for result in results if result[3])
    total_commit_time = sum(result[4] for result in results if result[4] is not None)
    average_commit_time = total_commit_time / total_commits if total_commits > 0 else 0
    commit_percentage = (total_commits / num_simulations) * 100


    #On ajoute les statistiques dans le fichier csv
    with open('simulation_results.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([])
        writer.writerow(['Commit Percentage', commit_percentage])
        writer.writerow(['Average Commit Time', round(average_commit_time,2)])
    print('fin de la simulation')

if __name__ == "__main__":
    main()

