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
      attr['label'] = place.name.upper() + ', C=%d' % len(place.tokens)
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

            a = str(result[1])
            b = str(result[3])
            dir = bool(int(result[5]))
            k = int(result[7])

            self.applyPredicate(a, b, dir, k)

   def applyPredicate(self, left, right, dir, k):
      if dir == True:
         pred = left
         succ = right
      else:
         pred = right
         succ = left

      if not self.pnet.has_transition(pred) and not self.pnet.has_transition(succ):
         # Buffer
         self.buildBuffer(pred, succ, dir, k)
      elif self.pnet.has_transition(pred):
         assert k == 1
         self.buildBranch(pred, succ, dir)
      elif self.pnet.has_transition(succ):
         assert k == 1
         self.buildBranch(succ, pred, dir)
      else:
         assert False

   def buildPlace(self, capacity):
      pname = 'p' + str(self.place_counter)
      self.place_counter += 1
      place = Place(pname, range(capacity))
      self.pnet.add_place(place)
      return str(place)

   def buildBranch(self, root, branch, dir):
      n = self.pnet

      assert(n.has_transition(root))

      if not self.pnet.has_transition(branch):
         n.add_transition(Transition(branch))
         branch_is_new = True
      else:
         branch_is_new = False

      if dir:
         # root --> branch (choice)
         root_output = n.transition(root).output()

         assert(len(root_output) == 1)

         input_place = str(root_output[0][0])
         try : n.add_input(input_place, branch, Value(1))
         except ConstraintError : print(sys.exc_info()[1])

         if branch_is_new:
            output_place = self.buildPlace(1)
            n.add_output(output_place, branch, Value(1))
      else:
         # root <-- branch (marge)
         root_input = n.transition(root).input()

         assert(len(root_input) == 1)

         output_place = str(root_input[0][0])
         n.add_output(output_place, branch, Value(1))

         if branch_is_new:
            input_place = self.buildPlace(1)
            try : n.add_input(input_place, branch, Value(1))
            except ConstraintError : print(sys.exc_info()[1])

   def buildChoice(self, pred, succ):
      # pred -- exists
      # succ -- new
      if not self.pnet.has_transition(succ):
         self.pnet.add_transition(Transition(succ))
         succ_is_new = True
      else:
         succ_is_new = False
      pred_output = self.pnet.transition(pred).output()

      assert(len(pred_output) == 1)

      l_place = str(pred_output[0][0])
      try : self.pnet.add_input(l_place, succ, Value(1))
      except ConstraintError : print(sys.exc_info()[1])

      if succ_is_new:
         r_place = self.buildPlace(1)
         self.pnet.add_output(r_place, succ, Value(1))

   def buildMerge(self, pred, succ):
      # pred -- new
      # succ -- exists
      if not self.pnet.has_transition(pred):
         self.pnet.add_transition(Transition(pred))
         pred_is_new = True
      else:
         pred_is_new = False
      succ_input = self.pnet.transition(succ).input()

      assert(len(succ_input) == 1)

      if pred_is_new:
         l_place = self.buildPlace(1)
         try : self.pnet.add_input(l_place, pred, Value(1))
         except ConstraintError : print(sys.exc_info()[1])

      r_place = str(succ_input[0][0])
      self.pnet.add_output(r_place, pred, Value(1))

   def buildBuffer(self, tr_1, tr_2, dir, k):
      n = self.pnet

      if dir:
         pred = tr_1
         succ = tr_2
      else:
         pred = tr_2
         succ = tr_1

      #if not n.has_transition(pred):
      n.add_transition(Transition(pred))

      #if not n.has_transition(succ):
      n.add_transition(Transition(succ))

      l_place = self.buildPlace(k)
      m_place = self.buildPlace(k)
      r_place = self.buildPlace(k)

      try : self.pnet.add_input(l_place, pred, Value(1))
      except ConstraintError : print(sys.exc_info()[1])

      n.add_output(m_place, pred, Value(1))

      try : n.add_input(m_place, succ, Value(1))
      except ConstraintError : print(sys.exc_info()[1])

      self.pnet.add_output(r_place, succ, Value(1))

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

