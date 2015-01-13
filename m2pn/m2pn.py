import os
import sys
import argparse
from collections import defaultdict
from pyparsing import *

#from pygraph.classes.graph import graph
#from pygraph.classes.digraph import digraph
#from pygraph.readwrite.dot import write
from snakes.nets import *
import snakes.plugins
snakes.plugins.load('gv', 'snakes.nets', 'nets')
from nets import *

separator = Word(",")
event_name = Word(alphanums + "-_\\")
m_pattern = "m(" + \
            event_name + "," + \
            event_name + "," + \
            Word("01") + "," + \
            Word(nums) + ")"

comment_line = Optional(Word(alphanums + ' \t')) + LineEnd().suppress()
aux_pattern = OneOrMore(LineEnd()) | ("#" + comment_line)

class PredicateParser:
   m_file = './example.m'
   place_counter = 0

   def __init__(self, m_file):
      self.m_file = m_file
      self.pnet = PetriNet(m_file + '.p')

   def draw(self, g_file):
      # Manual drawing
      #nodemap = dict((node.name, "node_%s" % num)
      #               for num, node in enumerate(self.pnet.node()))
      #g = self.pnet._copy(nodemap, self.pnet.clusters, None, None, None)
      #self.pnet._copy_edges(nodemap, g, None)
      #print(g.dot())
      #g.render(g_file, debug=True)

      # Using SNAKES.gv plugin interface
      self.pnet.draw(g_file,
                     engine = 'dot',
                     place_attr = self.draw_place,
                     trans_attr = self.draw_transition,
                     debug = True)

   def draw_place(self, place, attr) :
      attr['label'] = place.name.upper()
      attr['color'] = '#FF0000'

   def draw_transition(self, trans, attr) :
      if str(trans.guard) == 'True' :
         attr['label'] = trans.name
      else:
         attr['label'] = '%s\n%s' % (trans.name, trans.guard)

   def run(self):
      if not os.path.isfile(self.m_file):
         raise IOError('File ' + self.m_file + ' not found')
      file = open(self.m_file, "r")
      self.parseFile(file)
      file.close()

   def parseFile(self, file):
      for line in file:
         try:
            result = m_pattern.parseString(line)
         except Exception:
            try:
               result = aux_pattern.parseString(line)
            except Exception:
               print('[error] Invalid m-predicate format: "' + line + '"')
         else:
            sys.stdout.write('Parsing line: ' + line)

            a = result[1]
            b = result[3]
            dir = bool(result[5])
            k = int(result[7])

            self.applyPredicate(a, b, dir, k)

   def applyPredicate(self, left, right, dir, k):
      #if not self.pnet.has_transition(left):
      self.pnet.add_transition(Transition(left))

      #if not self.pnet.has_transition(right):
      self.pnet.add_transition(Transition(right))

      pname = 'p' + str(self.place_counter)
      self.place_counter += 1
      self.pnet.add_place(Place(pname, range(k)))

      try : self.pnet.add_input(pname, left, Value(1))
      except ConstraintError : print(sys.exc_info()[1])

      self.pnet.add_output(pname, left, Value(1))

      try : self.pnet.add_input(pname, right, Value(1))
      except ConstraintError : print(sys.exc_info()[1])

      self.pnet.add_output(pname, right, Value(1))

def main(argv):
   #Parse the m-predicate file
   parser = argparse.ArgumentParser(description='...')
   parser.add_argument('--input_file', '-if', help='specify an input file')
   parser.add_argument('--output_file', '-of', help='specify an output file')
   args = parser.parse_args(argv[1:])

   print('Starting ' + argv[0] + ' ...')

   m2pn = PredicateParser(args.input_file)

   if args.input_file:
      m2pn.run()
   else:
      print('[error] Need to specify an m-predicate file.\n')

   if args.output_file:
      m2pn.draw(args.output_file)
   else:
      print('[error] Need to specify a GraphViz output file.\n')

if __name__ == "__main__":
   main(sys.argv)

