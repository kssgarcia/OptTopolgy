# %%
import matplotlib.pyplot as plt
import numpy as np

from ESO_utils import *
from beams import *

# Solidspy 1.1.0
import solidspy.postprocesor as pos 
np.seterr(divide='ignore', invalid='ignore')

# %%
length = 20
height = 10
nx = 50
ny= 20
nodes, mats, els, loads, BC = beam(L=length, H=height, nx=nx, ny=ny, n=2)
elsI,nodesI = np.copy(els), np.copy(nodes)

IBC, UG = preprocessing(nodes, mats, els, loads)
UCI, E_nodesI, S_nodesI = postprocessing(nodes, mats[:,:2], els, IBC, UG)

# %%
niter = 200
RR = 0.005
ER = 0.005
V_opt = volume(els, length, height, nx, ny) * 0.50
ELS = None
for _ in range(niter):

    # Check equilibrium
    if not is_equilibrium(nodes, mats, els, loads) or volume(els, length, height, nx, ny) < V_opt: 
        print('Is not equilibrium')
        break
    
    # FEW analysis
    IBC, UG = preprocessing(nodes, mats, els, loads)
    UC, E_nodes, S_nodes = postprocessing(nodes, mats[:,:2], els, IBC, UG)

    # Compute Sensitivity number
    sensi_number = sensi_el(nodes, mats, els, UC)
    mask_del = sensi_number < RR
    mask_els = protect_els(els, loads, BC)
    mask_del *= mask_els
    ELS = els
    
    # Remove/add elements
    els = np.delete(els, mask_del, 0)
    del_node(nodes, els)

    RR += ER

# %%
pos.fields_plot(elsI, nodes, UCI, E_nodes=E_nodesI, S_nodes=S_nodesI)

# %%
pos.fields_plot(ELS, nodes, UC, E_nodes=E_nodes, S_nodes=S_nodes)

# %%
fill_plot = np.ones(E_nodes.shape[0])
plt.figure()
tri = pos.mesh2tri(nodes, ELS)
plt.tricontourf(tri, fill_plot, cmap='binary')
plt.axis("image");