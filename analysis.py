
import networkx as nx
import operator
from networkx.algorithms import bipartite
import matplotlib.pyplot as plt


def divNameParty(node):
    spl = node.split(" ")
    name = " ".join(spl[:2])
    party = " ".join(spl[2:])
    return name, party

def splitNodes(G):
    atts = nx.get_node_attributes(G,'bipartite')
    word_nodes = set()
    mp_nodes = set()
    for n in nx.nodes(G):
        if atts[n] == 1:
            word_nodes.add(n)
        else:
            mp_nodes.add(n)
    return word_nodes, mp_nodes

if __name__ == "__main__":
    G = nx.read_graphml("okrojony.graphml")

    word_nodes, mp_nodes = splitNodes(G)

    partyNameDict = {'Polskie Stronnictwo Ludowe': 'PSL', 'vel sęk PiS': 'PiS', '': 'N'}
    mapDict = {}
    nodesToReplace = {}
    for mp in mp_nodes:
        name, party = divNameParty(mp)
        if party in partyNameDict:
            newName = name + " " + partyNameDict[party]
            mapDict[mp] = newName
            nodesToReplace[mp] = newName
    
    for oldName, newName in nodesToReplace.items():
        mp_nodes.remove(oldName)
        mp_nodes.add(newName)

    G = nx.relabel_nodes(G, mapDict)
    parties = set()
    for n in mp_nodes:
        name, party = divNameParty(n)
        parties.add(party)

    
    partiesWords = dict() 

    
    for mp in mp_nodes:
        name, party = divNameParty(mp) 
        lgth = 0
        for n in G.neighbors(mp):
            lgth += 1
        if party in partiesWords:
            partiesWords[party] += lgth
        else:
            partiesWords[party] = lgth
            
    
    wordParties = dict()
    mpWordCnt = dict()
    for mp in mp_nodes:
        mpWordCnt[mp] = 0
        for n in G.neighbors(mp):
            mpWordCnt[mp] += 1


    for mp in mp_nodes:
        name, party = divNameParty(mp)
        if party not in wordParties:
            wordParties[party] = dict()
        for word in G.neighbors(mp):
            if word in wordParties[party]:
                wordParties[party][word] += G[mp][word]['weight']
            else:
                wordParties[party][word] = G[mp][word]['weight']


    
    for party, wordList in wordParties.items():
        wordParties[party] = sorted(wordList.items(), key=lambda x: x[1], reverse=True)
    


    WP = bipartite.weighted_projected_graph(G, mp_nodes)
    mpSimil = dict()
    for wpNode in WP:
        mpSimil[wpNode] = dict()
        for key, value in WP[wpNode].items():
            name, party = divNameParty(key)
            if party in mpSimil[wpNode]:
                mpSimil[wpNode][party] += value['weight']/partiesWords[party]/mpWordCnt[wpNode]*10000 
            else:
                mpSimil[wpNode][party] = value['weight'] /partiesWords[party]/mpWordCnt[wpNode]*10000  
    
    prctgOfCorrectParties = 0
    for mp in mp_nodes:
        hgst = sorted(mpSimil[mp].items(), key=lambda x: x[1], reverse=True)[0][0]
        name, party = divNameParty(mp)
        if hgst == "PiS":
            prctgOfCorrectParties += 1


    print("percetage: ", prctgOfCorrectParties*100/481)

    f=open("newold.txt", "w+", encoding='utf8')
    alreadyUsed = set()
    for key, val in mpSimil.items():
        name, party = divNameParty(key)
        for k, v in mpSimil.items():
            n, p = divNameParty(k)
            if name in k and key != k and name not in alreadyUsed:
                if party not in val:
                    val[party] = 0
                if party not in v:
                    v[party] = 0
                if p not in val:
                    val[p] = 0
                if p not in v:
                    v[p] = 0

                oldOld = val[party] #stara waga polaczen ze stara partia
                oldNew = val[p]#stara waga polaczen z nowa
                newOld = v[party] #nowa waga polaczen ze stara partia
                newNew = v[p] # nowa waga polaczen z nowa partia

                lossLinksCnt = '%.0f' % ((oldOld - newOld)/mpWordCnt[key]) #stracone polaczenia ze stara partia
                newLinksCnt = '%.0f' % ((newNew - oldNew)/mpWordCnt[k]) #nowo utworzone połączenia
                alreadyUsed.add(name)
                f.write(name + " " + party + " - " + p + ":\n")
                f.write("stracone połaczenia ze starą partią: " +  lossLinksCnt + "\n")
                f.write("nowo utworzone połączenia z nową partią: " + newLinksCnt + "\n")
                f.write("\n \n")
                break
    f.close()




    alreadyUsed = set()
    f=open("simil.txt", "w+", encoding='utf8')
    for key, val in mpSimil.items():
        name, party = divNameParty(key)
        for k, v in mpSimil.items():
            if name in k and key != k and name not in alreadyUsed:
                alreadyUsed.add(name)
                f.write(key + ": \n")
                for p1, simil1 in val.items():
                    if p1 != 'Republikanie' and p1 != 'Mniejszość Niemiecka':
                        s1 = '%.0f' % simil1
                        f.write(p1 + ": " + s1 + "; ")

                f.write("\n")

                f.write(k + ": \n")
                for p2, simil2 in v.items():
                    if p2 != 'Republikanie' and p2 != 'Mniejszość Niemiecka':
                        s2 = '%.0f' % simil2
                        f.write(p2 + ": " + s2 + "; ")
                
                f.write("\n \n")


    f.close()
    print(nx.info(WP))
    changesGraph = WP
    nodesToDel = set()
    for cgNode in changesGraph:
        name, party = divNameParty(cgNode)
        delNode = True
        for c in changesGraph:
            if c != cgNode and name in c:
                delNode = False
                break
        if delNode:
            nodesToDel.add(cgNode)

    for n in nodesToDel:
        changesGraph.remove_node(n)
    print(nx.info(changesGraph))
            



    nx.draw_circular(changesGraph)
    plt.draw()
    plt.show()

