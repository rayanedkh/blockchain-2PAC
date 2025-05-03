# Blockchain Consensus 2PAC Implementation and Comparison with GradedDAG

This project focuses on the implementation of the **2PAC BIG** blockchain consensus protocol and its comparison with the GradedDAG protocol. **2PAC BIG** is a more complex variant of the 2PAC protocol, developed as a response to the vulnerability found in the **Ditto** consensus of Facebook's **Diem** blockchain, as they announced in their paper [Diem's Paper on Jolteon and Ditto](https://arxiv.org/pdf/2106.10362). This project aimed to demonstrate that **2PAC BIG** is faster and more efficient in certain scenarios compared to the previous state-of-the-art asynchronous blockchain consensus protocols **GradedDAG**.

## M. Rambaud Publication
The full paper can be found here: [2PAC Paper](https://eprint.iacr.org/2024/1108.pdf).

## Project Overview

In this project, we conducted simulations to evaluate how the **2PAC BIG** protocol performs under network conditions where GradedDAG struggles, particularly in terms of block commitment. The simulation focused on varying delays between nodes, especially node 4, which has a random delay based on a normal distribution with a mean of 0 seconds and a standard deviation of 0.7 seconds (we use the absolute value of this delay). This allowed us to test the protocols under conditions that would highlight the key differences in performance between 2PAC and GradedDAG.

### Key Delay Conditions:
1. **When node 4’s additional delay is less than delta_fast (the communication delay between other nodes which is 0.5s)** the communication delay `delta` (`delta_fast + (additional_delay)/2`) is less than `3/2 * delta_fast`. In this case, both 2PAC and GradedDAG can commit blocks.
2. **When node 4’s additional delay is between delta_fast and 2*delta_fast (between 0.5s and 1s)**, the communication delay `delta` falls between `3/2 * delta_fast` and `2 * delta_fast`. This is the key scenario where the difference between the two protocols becomes evident. In this range, **2PAC can commit blocks**, but **GradedDAG cannot**. This happens in approximately 32% of the cases according to the chosen normal distribution.
3. **When node 4’s additional delay is greater than 2*delta_fast (1s)**, the communication delay `delta` becomes greater than `2 * delta_fast`. In this case, neither 2PAC nor GradedDAG can commit blocks, as both protocols face synchronization issues.

Thus, the key differentiator between 2PAC and GradedDAG lies in the **delay between 0.5s and 1s**, which occurs in about 8% of the total cases (`0.32 / 4 = 8%`), where 2PAC is able to commit blocks while GradedDAG cannot.

### Key Challenges:
One of the main difficulties in implementing the **2PAC BIG** protocol was handling simultaneous communication between nodes using **multithreading** and **sockets**. We introduced **precise delays** on a single node (node 4) to simulate real-world conditions or a corrupted node. Managing the multithreading environment while ensuring accurate timing and synchronization was particularly difficult, especially when introducing specific delays on just one node. Ensuring that messages were sent and received in the correct order while handling potential delays required complex threading mechanisms and robust error handling to avoid deadlocks and race conditions.

### Theoretical Commit Success Difference:
As we've seen, **2PAC is expected to have a commit success rate that is 8% higher than GradedDAG** under these delay conditions. Our simulation results show a **7.2% improvement** in commit success for 2PAC after 1000 simulations, which closely aligns with the theoretical 8% difference mentioned in the paper. While 1000 simulations provided a clear result, further simulations would be necessary for a more statistically significant comparison, particularly with more extensive node networks.

## Files:
The project is structured into two main directories: **2PAC** and **GradedDAG**. Both directories contain the following files (which implement similar functionalities for each protocol):

1. **`main.py`**: The main script for running simulations, including setting up nodes, broadcasting blocks, and monitoring the commit process.
2. **`stats.py`**: Contains the logic for running multiple simulations, collecting results, and saving them to CSV files for analysis.
3. **`node.py`**: Implements the `Node` class, which represents each node in the network, including its message handling and state management.
4. **`com.py`**: Handles the communication logic between nodes using sockets and threads.
5. **`data_struct.py`**: Defines the data structures for blocks, votes, leader election, and messages exchanged between nodes.
6. **`sign.py`**: Provides methods for generating key pairs, signing messages, and verifying signatures for secure communication.
7. **`tools.py`**: Provides utility functions for serializing data and preparing messages for transmission.
8. **`simulation_protocolname.csv`**: Results of the 1000 simulations for the protocol.

## How to Run the Simulation

### Prerequisites:
To run this project, you'll need to install the following Python dependencies:
```bash
pip install pynacl numpy
```

### Running a Single Simulation:
To run a single simulation of 2PAC BIG and see the commit results, execute the following:
```bash
python main.py 0.8
```

This will simulate the process (with 0.8s delay on node n°4), output the commit status to the console, and log the actions taken by each node during the simulation.

### Running Multiple Simulations:
To run 1000 simulations and store the results in CSV files, execute stats.py with the following command:
```bash
python stats.py
```

This will run 1000 simulations, collect the results, and save them in simulation_results.csv.
