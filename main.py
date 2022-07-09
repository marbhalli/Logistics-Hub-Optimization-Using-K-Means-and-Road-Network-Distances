import sys

sys.path.append(r'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization')

import hub_optimization

import variables

starting_centroids = variables.starting_centroids

n_iterations = variables.n_iterations

cutoff = variables.cutoff

print()

if variables.BOOL_WEIGHT :
    print('weighted algorithm is being performed')
    print()
else :
    print('non-weighted algorithm is being performed')
    print()

print(f'Total iterations are {n_iterations}')
print()

print(f'cutoff value : {cutoff}')
print()

print(f'starting points : {starting_centroids}')
print()
print('---------------------------------------------')

hub_optimization.main(n_iterations,starting_centroids,cutoff)

print('Finished')











