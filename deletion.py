import networkx as nx
from networkx.algorithms import bipartite
import csv

relWords = []

with open('Wynik.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter='\t')
    line_count = 0
    for row in csv_reader:
        relWords.append(row[2])

G = nx.read_graphml('testgraphml.graphml')

print(nx.is_bipartite(G))
print(nx.is_connected(G))
word_nodes, mp_nodes = bipartite.sets(G)
wordsToDel = ['poseł', 'klub', 'głos', 'poprawka', 'osoba', 'porządek', 'marszałek', 'stanowisko', 'strona','premier','cel','praca','lato','zasada', 'ręka']


numOfDel = 0
for word in word_nodes:
    if word not in relWords or word in wordsToDel:
        G.remove_node(word)
        numOfDel +=1




print(numOfDel)

G.remove_nodes_from(list(nx.isolates(G)))

print(nx.number_of_edges(G))
print(nx.number_of_nodes(G))
nx.write_graphml(G, "okrojony.graphml")
sortedEdges = sorted(G.edges(data=True),key= lambda x: x[2]['weight'],reverse=True)


print('a')