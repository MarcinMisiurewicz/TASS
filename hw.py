import networkx as nx
from networkx.algorithms import bipartite

G = nx.read_gml('test.gml')

print(nx.number_of_nodes(G))
print(nx.number_of_edges(G))

mp_nodes, word_nodes = bipartite.sets(G)

for id in mp_nodes


sortedEdges = sorted(G.edges(data=True),key= lambda x: x[2]['weight'],reverse=True)



