import networkx as nx
import pickle as pkl


def filter_nodes(G, countries):
    new_nodes = \
        [n for n in G.nodes() if n in countries]
    subG = G.subgraph(new_nodes)
    return subG

def filter_edges(G, min_kusd=5e4):
    new_edges = \
        [(u, v) for u, v, d in G.edges(data=True) if d['weight'] >= min_kusd]
    subG = G.edge_subgraph(new_edges)
    return subG

def create_output_complete_subG(G, countries):
    # create subgraph with all flows involving m
    subG = nx.DiGraph()
    for country in countries:
        subG.add_node(country)
    for edge in G.edges():
        if edge[0] in countries:
            subG.add_edge(
                edge[0], edge[1],
                weight=G.edges[edge]['weight'])
    return subG

def check_gamma(subG):
    # check if output is complete
    # |ncountries| - |nflows| + |ncycles|
    # = 0
    ncountries = len(subG.nodes())
    nflows = len(subG.edges())
    simple_cycles = list(nx.algorithms.cycles.simple_cycles(subG))
    ncycles = len(simple_cycles)
    gamma = - ncountries + nflows - ncycles
    return gamma, ncountries, nflows, ncycles, simple_cycles

def asia_subG(G):
    with open ('asia.txt', 'rb') as fp:
        asia = pkl.load(fp)
    subG = G.subgraph(asia)
    return subG