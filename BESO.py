# %%
import matplotlib.pyplot as plt
import numpy as np
from opt_beam import *
from beams import *
from ESO_utils import *
# Solidspy 1.1.0
import solidspy.postprocesor as pos 

np.seterr(divide='ignore', invalid='ignore')

# %%
length = 8
height = 5
nx = 40
ny= 30
nodes, mats, els, loads, BC = beam_2(L=length, H=height, nx=nx, ny=ny)

elsI,nodesI = np.copy(els), np.copy(nodes)
IBC, UG, _ = preprocessing(nodes, mats, els, loads)
UCI, E_nodesI, S_nodesI = postprocessing(nodes, mats, els, IBC, UG)

# %%
niter = 100
ER = 0.01
t = 0.01

r_min = np.linalg.norm(nodes[0,1:3] - nodes[1,1:3]) * 1.5
adj_nodes = adjacency_nodes(nodes, els)
centers = center_els(nodes, els)

Vi = volume(els, length, height, nx, ny)
V_opt = Vi.sum() * 0.30

# Initialize variables.
ELS = None
mask = np.ones(els.shape[0], dtype=bool)
sensi_I = None
C_h = np.zeros(niter)
error = 1000

for i in range(niter):
    # Calculate the optimal design array elements
    els_del = els[mask].copy()
    V = Vi[mask].sum()

    # Check equilibrium
    if not is_equilibrium(nodes, mats, els_del, loads): 
        print('Is not equilibrium')
        break
    
    # Storage the solution
    ELS = els_del

    # FEW analysis
    IBC, UG, rhs_vec = preprocessing(nodes, mats, els_del, loads)
    UC, E_nodes, S_nodes = postprocessing(nodes, mats, els_del, IBC, UG)

    # Sensitivity filter
    sensi_e = sensitivity_els(nodes, mats, els, mask, UC)
    sensi_nodes = sensitivity_nodes(nodes, adj_nodes, centers, sensi_e) #3.4
    sensi_number = sensitivity_filter(nodes, centers, sensi_nodes, r_min) #3.6

    # Avrage the sensitivity numbers to the historical information 
    if i > 0: 
        sensi_number = (sensi_number + sensi_I)/2 # 3.8
    sesni_number = sensi_number/sensi_number.max()

    # Check if the optimal volume is reached and calculate the next volume
    V_r = False
    if V <= V_opt:
        els_k = els_del.shape[0]
        V_r = True
        break
    else:
        V_k = V * (1 + ER) if V < V_opt else V * (1 - ER)

    # Remove/add threshold
    sensi_sort = np.sort(sensi_number)[::-1]
    els_k = els_del.shape[0]*V_k/V
    alpha_del = sensi_sort[int(els_k)]

    # Remove/add elements
    mask = sensi_number > alpha_del
    mask_els = protect_els(els[np.invert(mask)], els.shape[0], loads, BC)
    mask = np.bitwise_or(mask, mask_els)
    del_node(nodes, els[mask], loads, BC)

    # Calculate the strain energy and storage it 
    C = 0.5*rhs_vec.T@UG
    C_h[i] = C
    if i > 10: error = C_h[i-5:].sum() - C_h[i-10:-5].sum()/C_h[i-5:].sum()

    # Check for convergence
    if error <= t and V_r == True:
        print("convergence")
        break

    # Save the sensitvity number for the next iteration
    sensi_I = sensi_number.copy()

# %%
pos.fields_plot(elsI, nodes, UCI, E_nodes=E_nodesI, S_nodes=S_nodesI)

# %%
pos.fields_plot(ELS, nodes, UC, E_nodes=E_nodes, S_nodes=S_nodes)
