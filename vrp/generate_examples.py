#!/usr/bin/env python
# coding: utf-8


# libraries
import networkx as nx
import random
import numpy as np
import itertools
import pyomo.environ as pe
import pyomo
import pandas as pd
import os.path
import cloudpickle

def get_example(num_customers, solomon):
    number, capacity, dtimes, demand_array, ready_array, due_array, service_array = parse_problem(solomon, num_customers, tfac = 1)
    time_table = pd.DataFrame({'customer_id':[0],
                                 'e_i':[0],                                                                  
                                 'l_i':[np.inf],                                                             
                                 's_i':[0]})
    population_size = len(demand_array)
    for ix in range(1, num_customers + 1):
        customer_id = np.random.randint(1, population_size)
        e_i, l_i = ready_array[customer_id], due_array[customer_id]
        s_i = service_array[customer_id]
        new_entry = [customer_id, e_i, l_i, s_i]
        time_table.loc[ix] = new_entry

    return time_table, dtimes

def parse_problem(name, num_customers, tfac = 1): 
    num_examples = (num_customers//100) + 1
    lines=[]
    for example_ix in range(num_examples):
        filename='./problems/' + name[:-1] + str(example_ix+1)+ '.txt'
        with open(filename) as csvfile:                                                                          
            lines_ix = csvfile.readlines()                                                                          
        lines.append(lines_ix)
    lines = list(itertools.chain.from_iterable(lines))
    demand = []                           
    coord = []                           
    ready = []                          
    due = []                           
    service = []                      
    for ix,line in enumerate(lines):                                                                               
        row = line.split()                                                                           
        if len(row) == 2 and row[0][0].isdigit():                                                    
            number = int(row[0])                                                                     
            capacity = int(row[1])                                                                   
        if len(row) < 5 or not row[0][0].isdigit():                                                  
            continue                                                                                 
        coord.append(np.array([tfac*float(row[1]), tfac*float(row[2])]))  
        demand.append(float(row[3]))                                     
        ready.append(tfac*float(row[4]))                                
        due.append(tfac*float(row[5]))                                 
        service.append(tfac*float(row[6]))                            
    n = len(demand)   
    dtimes = np.zeros((n,n))
    for i in range(n):                                                                                   
        for j in range(n):                                                                               
            dtimes[i,j] = np.linalg.norm(coord[i] - coord[j])                                            
    return number, capacity, dtimes, np.array(demand), np.array(ready), np.array(due), np.array(service)

def generate_examples_list(num_customers_vals, N, solomon_list, outfile):
    ###### Size of Problem
    # num_customers_vals: numberof customers in each example
    # N:                  number of examples to generate
    # solomon_list:       list of solomon problem types

    ### Example:
    # num_customers_vals = [5, 10, 25, 50]
    # N = 5
    # solomon_list = ['r101', 'c101', 'r201', 'c201']  
    # outfile = 'examples_list.txt'
    np.random.seed(0)
    examples_list = []
    for solomon in solomon_list:
        for num_customers in num_customers_vals:
            for i in range(N):
                # check if example exists
                params = [str(item) for item in [num_customers, i, solomon]]
                string_list = ['num_customers', 'i', 'solomon']
                param_settings = map(lambda atuple: atuple[0]+'='+atuple[1], zip(string_list, params))
                param_string = '_'.join(param_settings)
                example_file_name = 'example_' + param_string + '.pickle'
                examples_list.append('examples/'+example_file_name)
                if os.path.isfile('examples/'+example_file_name):
                    print('pickle file already exists, continuing')
                    continue
    
                # If not, then create example, and pickle it 
                print('creating new example ', example_file_name)
                example = get_example(num_customers, solomon)
                        
                with open('examples/'+example_file_name, 'wb') as f:
                    cloudpickle.dump(example, f)
       
    with open(outfile, 'w') as f:
        for line in examples_list:
            f.write(line[:-7]+'\n')
