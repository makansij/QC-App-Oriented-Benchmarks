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
import milp

# remove 
import sys
import generate_all_routes
import main_sequential
from VRPTW import *

class Result:
    def __init__(self, time, objective_val, data):
        self.time = time
        self.objective_val = objective_val
        self.data = data

def save_model_and_results(example_string, solution_method, result, parameters=None):
    results_file_name = example_string  + '_solution_method=' + solution_method + '_result' +  '.pickle'
    if os.path.isfile(results_file_name):
      try:
        os.remove(results_file_name)
      except:
        pass
    with open(results_file_name, 'wb') as f:
        cloudpickle.dump(result, f)

 
if __name__ == "__main__":
    ##'python3 main.py  --examples_list examples_list.txt --solution_method insertion'
    parser = argparse.ArgumentParser(description='solve example given')
    parser.add_argument('--examples_list', type=str, default='', help='what examples_list? ')
    parser.add_argument('--solution_method', type=str, default='', help='what solution_method ')
    args = parser.parse_args()
    examples_list_file_name = args.examples_list
    solution_method = args.solution_method
    if solution_method not in ['insertion', 'annealing', 'milp']:
        raise ValueError('solution method must be either insertion or annealing')

    with open(examples_list_file_name, 'r') as file:
        for line in file:
            string = line.strip()
            example_string = string[9:]
            with open(string+'.pickle', 'rb') as f:
                time_table, dist_matrix = cloudpickle.load(f)
            
            # convert to time_windows
            time_windows = list(zip(time_table.e_i.values, time_table.l_i.values))
            service_times = list(time_table.s_i.values)
            n_customers = len(service_times)-1
            
            # create dataframe
            df = pd.DataFrame(columns=['demand', 's_i', 'e_i', 'l_i'])
            df.demand = [0]*len(time_windows)
            df.e_i = [elm[0] for elm in time_windows]
            df.l_i = [elm[1] for elm in time_windows]
            df.s_i = service_times
            df.loc[0] = [0,0,0,np.inf]
            #df.drop(len(df)-1, axis=0, inplace=True)
  
            if solution_method=='milp':
                (total_time, objective, data) = milp.solve_milp(df, dist_matrix, n_customers)
 
            if solution_method=='insertion': 
                # #### SOLVE USING INSERTION
                travel_times = dist_matrix
                distance_matrix = dist_matrix
                start_time_insertion = time.time()
                all_routes_service_times_tuples, routed_customers = generate_all_routes.generate_all_routes(df, travel_times, distance_matrix)
                end_time_insertion = time.time()
                total_time = end_time_insertion - start_time_insertion
            
                # # run sanity check and get objective value
                max_tour_length=6000
                max_capacity=500
                generate_all_routes.sanity_check(all_routes_service_times_tuples, df, distance_matrix, travel_times, max_tour_length=max_tour_length, max_capacity=max_capacity)
                routes = [atuple[0] for atuple in all_routes_service_times_tuples]
                distance_matrix = dist_matrix
                cost = calculate_cost(routes, distance_matrix)
                print('\n the cost is ', cost, '\n')    

                objective = cost
                data = all_routes_service_times_tuples

            elif solution_method=='annealing': 
                #### SOLVE USING ANNEALING
                travel_times = dist_matrix
                distance_matrix = dist_matrix
                all_routes_service_times_tuples = []
                start_time_annealing = time.time()
                best_solution, cost = simulated_annealing_multi(df, travel_times, time_windows, service_times)
                end_time_annealing = time.time()
                total_time = end_time_annealing - start_time_annealing
            
                for route in best_solution:
                    service_start_times = generate_all_routes.get_initial_service_start_times(route, df, travel_times)
                    all_routes_service_times_tuples.append((route,  service_start_times))
            
                max_tour_length=6000
                max_capacity=6000
                generate_all_routes.sanity_check(all_routes_service_times_tuples, df, distance_matrix, travel_times, max_tour_length=max_tour_length, max_capacity=max_capacity)

                objective = cost
                data = all_routes_service_times_tuples

            # create results object and save pickle file
            result = Result(total_time, objective, data)
            save_model_and_results('results/'+example_string, solution_method, result, parameters=None)

