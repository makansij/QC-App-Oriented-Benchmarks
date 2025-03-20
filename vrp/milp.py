#!/usr/bin/env python
# coding: utf-8
import os
import subprocess
import time
import cloudpickle
import numpy as np
import pyomo.environ as pe
import scipy.io as sp_io
import argparse
import networkx as nx
import itertools
import pyomo
import pandas as pd
import pdb
import sys
from collections import defaultdict

def order_tuples(tuples):
    if not tuples:
        return []
    
    # Build adjacency lists
    adj = defaultdict(list)
    for a, b in tuples:
        adj[a].append((a, b))
        adj[b].append((a, b))
    
    # Start with the first tuple
    ordered = [tuples[0]]
    used = set(ordered)

    while len(ordered) < len(tuples):
        last = ordered[-1]
        last_elem = last[1]  # Look for tuples that connect to this

        for next_tuple in adj[last_elem]:
            if next_tuple not in used:
                ordered.append(next_tuple)
                used.add(next_tuple)
                break
    
    return ordered


def display_route(model, k, valid_arcs):
  route = []
  for i in model.all_customers:
      for j in model.all_customers:
          try:
            if all([i != j , (i,j,k) in valid_arcs, model.x[i, j, k].value > 0.5]):
                route.append((i,j))
          except:
              continue
  return route
    
def display_results(model, valid_arcs):
    print_str=''
    for k in range(model.max_vehicles):
        print_str_k='The route of vehicle k='+str(k)+': \n'
        route = display_route(model, k, valid_arcs)
        if route==[]:
            continue
        
        output_tuples = order_tuples(route)      
        for elm in output_tuples:
            print_str_k += '\t From node '+ str(elm[0]) + ' to node '+ str(elm[1]) +'\n'
        print_str += print_str_k
    print(print_str)
    
def solve_milp(df, dist_matrix, n_customers):
    start_time = time.time()

    # Model
    model = pe.ConcreteModel()
    model.max_vehicles = n_customers 
    model.n_customers = n_customers
    model.nodes = range(1, model.n_customers + 1)  # Customers (1, 2)
    model.all_customers = range(model.n_customers + 2)  # Includes depot (0), customers (1,2), and new node N
    N = model.n_customers + 1  # Artificial sink node
    
    # Construct valid index sets
    valid_arcs = set()
    
    # (0, i, k): Vehicle leaving depot to customer
    valid_arcs.update((0, i, k) for i in model.nodes for k in range(model.max_vehicles))
    
    # (i, j, k): Customer-to-customer travel
    valid_arcs.update((i, j, k) for i in model.nodes for j in model.nodes if i != j for k in range(model.max_vehicles))
    
    # (i, N, k): Vehicle traveling from customer to artificial sink N
    valid_arcs.update((i, N, k) for i in model.nodes for k in range(model.max_vehicles))
    
    # Define the decision variable with the valid index set
    model.x = pe.Var(valid_arcs, within=pe.Binary)
    
    # Time variables for all customer model.nodes + artificial sink N
    model.t = pe.Var(set(range(0,model.n_customers+2)) | {N}, within=pe.NonNegativeReals)  # Include N in time variables

    # Objective: Minimize total travel time
    model.obj = pe.Objective(
        expr=sum(dist_matrix[i][j] * model.x[i, j, k] for i in range(0,model.n_customers) for j in range(1,model.n_customers+1) for k in range(model.max_vehicles) if i!=j),
        sense=pe.minimize
    )
    
    # Constraints
    model.constraints = pe.ConstraintList()

    # Each vehicle leaves the depot at most once
    for k in range(model.max_vehicles):
        model.constraints.add(sum(model.x[0, j, k] for j in model.nodes) <= 1)
    
    # Each vehicle enters the sink node at most once
    for k in range(model.max_vehicles):
        model.constraints.add(sum(model.x[i, N, k] for i in model.nodes) <= 1)
    
    # If a vehicle is used, it must return to the sink
    for k in range(model.max_vehicles):
        model.constraints.add(sum(model.x[0, j, k] for j in model.nodes) == sum(model.x[i, N, k] for i in model.nodes))
    
    # Each customer is visited exactly once (all customers have an incoming arc) 
    for j in range(1,model.n_customers+1):  # Exclude depot, and exclude final depot
        model.constraints.add(sum(model.x[i, j, k] for i in range(0,model.n_customers+1) for k in range(model.max_vehicles) if i != j) == 1)
    
    # Vehicle flow conservation
    for k in range(model.max_vehicles):
        for j in range(1,model.n_customers+1):
            model.constraints.add(sum(model.x[i, j, k] for i in range(0, model.n_customers+1) if j != i) == sum(model.x[j, i, k] for i in range(1,model.n_customers+2) if j != i))
    
    ## Time window constraints
    for i in range(1,model.n_customers+1):
        model.constraints.add(df.e_i[i] <= model.t[i])
        model.constraints.add(model.t[i] <= df.l_i[i])
    #
    ## Subtour elimination (M-TSP-based)
    M = 10000  # Big-M constant
    for k in range(model.max_vehicles):
        for i in range(0,model.n_customers+1):
            for j in range(1,model.n_customers+2):
                if (i,j,k) in valid_arcs: 
                    if j==model.n_customers+1:
                        j_ix=0            
                    else:
                        j_ix=j
    
                    t_ij = dist_matrix[i][j_ix]
                    s_i = df.s_i[i]
                    model.constraints.add(model.t[j] >= model.t[i] + s_i + t_ij - M * (1 - model.x[i, j, k]))

    end_time = time.time()

    ## Solve
    solver = pe.SolverFactory('cbc')  # Replace with 'cplex', 'gurobi', etc.
    solver.solve(model, tee=False)

    # Display results
    display_results(model, valid_arcs)
    

    for k in range(model.max_vehicles):
        for i in model.all_customers:
            for j in model.all_customers:
                try:
                    if i != j and model.x[i, j, k].value > 0.5:
                        print(f'Vehicle {k} travels from {i} to {j}')
                except:
                    continue
                    import pdb
                    pdb.set_trace()
    
    for i in model.nodes:
        print(f'Node {i} arrival time: {model.t[i].value}, within time window (', df.e_i[i], df.l_i[i],' )')

    total_time = end_time - start_time
    objective = pe.value(model.obj)
    data = model

    return total_time, objective, data

# dummy

