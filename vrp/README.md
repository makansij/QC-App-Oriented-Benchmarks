# README

## Overview

This repository contains a script for generating and solving specific examples of a problem by specifying parameters such as:

- `num_customers_vals`: List of numbers indicating different customer sizes.
- `solomon_list`: Type of Solomon example (e.g., `r101`, `c201`).
- `N`: Number of random examples to generate for each combination of `num_customers_vals` and `solomon_list`.
- `outfile`: The name of the text file to store the names of the generated examples.

The generated examples are stored in the `examples/` sub-directory.

## Installation

Ensure you have Python installed. Then, install the required dependencies using:

```bash
pip install cloudpickle pandas numpy pyomo scipy networkx
```

## Usage

To run the script, use the following command:

```python
import time
import cloudpickle
import pandas as pd
import numpy as np
np.set_printoptions(linewidth=200)
import sys
import generate_examples
import milp
```

Modify the parameters inside the script as needed.

## Example

Here's an example usage of the script:

```python
# Define parameters
num_customers_vals = [5, 10, 15]
solomon_list = ['r101', 'c201']
N = 3
outfile = "example_list.txt"

# Generate examples
generate_examples.run(num_customers_vals, solomon_list, N, outfile)
```

## Solving the Example using MILP

Once the examples are generated, you can solve them using the MILP solver:

```python
# Load the generated example
df = pd.read_pickle("examples/example_1.pkl")
dist_matrix = np.load("examples/dist_matrix_1.npy")
n_customers = len(df)

# Solve the problem using MILP
(total_time, objective, data) = milp.solve_milp(df, dist_matrix, n_customers)

# Print or save the results
print(f"Total Time: {total_time}")
print(f"Objective Value: {objective}")
print("Solution Data:", data)
```

Ensure that the `milp.solve_milp` function is properly defined and configured to use an appropriate solver (e.g., Gurobi, CPLEX, or CBC).

## License

This project is licensed under the MIT License.


