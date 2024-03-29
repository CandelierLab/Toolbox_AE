import os, sys
import numpy as np

from AE.Network.ANN import ANN
from AE.Network.Comparison import compare, matching

os.system('clear')

# === Net definitions ======================================================

# --- Fist net -------------------------------------------------------------

NetA = ANN()

# Direct 3-nodes
NetA.add_node(1, IN=True)
NetA.add_node(1)
NetA.add_node(1, OUT=True)
NetA.add_edge(0, 1, w=1)
NetA.add_edge(1, 2, w=1)

# Fork
# # # NetA.add_node(1, IN=True)
# # # NetA.add_node(2)
# # # NetA.add_node(2, OUT=True)
# # # NetA.add_edge(0, 1, w=1)
# # # NetA.add_edge(0, 2, w=1)
# # # NetA.add_edge(1, 3, w=1)
# # # NetA.add_edge(2, 4, w=1)

# NetA.show()
# sys.exit()

# --- Second net -------------------------------------------------------------

NetB = ANN()

# Fork
NetB.add_node(1, IN=True)
NetB.add_node(2)
NetB.add_node(2, OUT=True)
NetB.add_edge(0, 1, w=1)
NetB.add_edge(0, 2, w=1)
NetB.add_edge(1, 3, w=0.6)
NetB.add_edge(2, 4, w=0)

# NetB.show()
# sys.exit()

# === Computation ==========================================================

# S_nodes, S_edges = compare(NetA, NetB)

# S_nodes = np.round(S_nodes*1e3)*1e-3
# S_edges = np.round(S_edges*1e3)*1e-3

# print('\n', S_nodes)
# print('\n', S_edges)

M = matching(NetA, NetB)

M.print()

# NetA.print()
