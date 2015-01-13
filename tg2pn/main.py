import os
import sys
import argparse
from collections import defaultdict
from pyparsing import Word, alphanums, nums, printables
from graph_tool.all import *

node_pattern = Word(alphanums + "_") + "[" + "fixedsize = box fillcolor = yellow" + "label= \"" + Word(alphanums + "_ \\") + "\"];"
edge_pattern = Word(alphanums + "_") + "->" + Word(alphanums + "_") + "[ label = \" \" ];"
buff_pattern = Word(alphanums + "_") + "->" + Word(alphanums + "_") + "[ style = dotted ];"
buffsize_pattern = "Buffer_" + Word(nums) + "_size_" + Word(nums)

def print_graph(g, node_table, v_type, v_cap, v_shape):
    v_prop = g.new_vertex_property("string")
    v_fillcolor = g.new_vertex_property("string");
    for v_label in node_table.keys():
        v = g.vertex(node_table[v_label])
        v_prop[v] = v_label if v_cap[v] == 0 else v_label + '\nc=' + `v_cap[v]`
        v_fillcolor[v] = "yellow" if v_type[v] == "node" else "lightgrey"

    graphviz_draw(g,
        vprops = {
            "label": v_prop,
            "fixedsize": "shape",
            "shape": v_shape,
            "width": "0.5",
            "fontsize": "24.0",
            "fillcolor": v_fillcolor
        },
        eprops = {
            "dir": "forward",
            "arrowhead": "normal",
            "arrowsize": 1
        },
        gprops = {
            "layout": "neato",
            "size": "20"
        },
        overlap = "scalexy",
        output = "graph-draw.pdf")

def createPNPlace(start_node, end_node):
    g = start_node.get_graph()
    place = g.add_vertex()
    index = g.vertex_index[place]
    g.add_edge(start_node, place)
    g.add_edge(place, end_node)
    return index

def taskGraph2PetriNet(g, node_table, v_type, v_cap):
    edges = list(g.edges())
    v_shape = g.new_vertex_property("string")
    old_edges = list()
    # [start_node] --edge--> [end_node]
    # Replace with
    # / start_node \ --edge11--> [place1] --edge12--> /          \
    # \            / --edge21--> [place2] --edge22--> \ end_node /
    i = 0
    for e in edges:
        start_node = e.source()
        end_node = e.target()
        if v_type[start_node] == "buffer" or v_type[end_node] == "buffer":
            continue
        index = createPNPlace(start_node, end_node)
        node_table["p" + `i`] = index
        v_shape[g.vertex(index)] = "circle"
        v_shape[start_node]      = "box"
        v_shape[end_node]        = "box"
        v_cap[g.vertex(index)]   = 1
        old_edges.append(e)
        i += 1

    for e in old_edges:
        g.remove_edge(e)

    return v_shape

def main(argv):
    parser = argparse.ArgumentParser(description='...')
    parser.add_argument('--file', '-f', help='...')
    args = parser.parse_args(argv[1:])

    print 'Starting Traces2PetriNet...'

    # label[i] -> vertex_id[i]
    node_table = {}
    g = Graph()

    #TODO replace node_table with the following property map:
    v_type = g.new_vertex_property("string")
    v_cap = defaultdict(lambda : 0)

    if args.file:
        fn = args.file
        if not os.path.isfile(fn):
            raise IOError('File ' + fn + ' not found')
        file = open(fn)
        for line in file:
            #print line
            try:
                result = node_pattern.parseString(line)
            except Exception:
                try:
                    result = edge_pattern.parseString(line)
                except Exception:
                    try:
                        result = buff_pattern.parseString(line)
                    except Exception:
                        print("[ No match ] " + line)
                    else:
                        print("[Found buff] " + line)

                        if result[0] in node_table:
                            v1 = g.vertex(node_table[result[0]])
                        else:
                            v1 = g.add_vertex()
                            node_table[result[0]] = g.vertex_index[v1]
                            v_type[v1] = "buffer"
                            subresult = buffsize_pattern.parseString(result[0])
                            v_cap[v1] = int(subresult[3])

                        if result[2] in node_table:
                            v2 = g.vertex(node_table[result[2]])
                        else:
                            v2 = g.add_vertex()
                            node_table[result[2]] = g.vertex_index[v2]
                            v_type[v2] = "buffer"
                            subresult = buffsize_pattern.parseString(result[2])
                            v_cap[v2] = int(subresult[3])

                        g.add_edge(v1, v2)

                else:
                    print("[Found edge] " + line)
                    g.add_edge(g.vertex(node_table[result[0]]),
                               g.vertex(node_table[result[2]]))
            else:
                print("[Found node] " + line)
                v = g.add_vertex()
                v_type[v] = "node"
                node_table[result[0]] = g.vertex_index[v]

        file.close()
        v_shape = taskGraph2PetriNet(g, node_table, v_type, v_cap)
        print_graph(g, node_table, v_type, v_cap, v_shape)

if __name__ == "__main__":
    main(sys.argv)

