import re

import util

# The general class for algorithms that try and solve for citations.
# The hope is that every algorithm extends Method in the same pattern
# and then they can be switched out.
# Utility methods (perhaps a special split string or stopword removal) should probably go in here.
# WARNING: A Method may maintain state data about the citations it has done.
#  This is very important in the cases that there are multiple cites in a single context (sentence, paragraph, etc).
#  Therefore, you should only use a method instance on one citation cycle (itteration through the paper).
class Method:
   # Return None if you can't make a guess.
   def guess(cite, paper):
      return None

class ProperNounMethod(Method):
   def __init__(self, paper):
      # Pre-build a list of all proper nouns in the references' title and authors.
      self.properNouns = {}

      # TODO(eriq): remove stopwords and try to remove other capitilization false positives.
      for (key, reference) in paper.references.items():
         # Make sure to avoid initials.
         authorNouns = re.findall('\w{2,}', ' '.join(reference.authors))
         self.properNouns[key] = set([authorNoun.upper() for authorNoun in authorNouns])

         self.properNouns[key] |= util.removeTitleStopwords(util.getCapitalWords(reference.title))

         #self.properNouns[key] |= util.getCapitalWords(reference.abstract)

      self.properNouns = util.uniqueSets(self.properNouns)

      #TEST
      for (ref, nouns) in self.properNouns.items():
         print "{0} -- {1}".format(ref, nouns)

      # There will be no more than one citation per reference per context (probably).
      self.contextHistory = {}

   def guess(self, cite, paper):
      words = util.getCapitalWords(cite.sentenceContext.noCitations)

      # Get the citation history for this context
      if not self.contextHistory.has_key(cite.sentenceContext.noCitations):
         self.contextHistory[cite.sentenceContext.noCitations] = set()
      history = self.contextHistory[cite.sentenceContext.noCitations]

      for (referenceKey, nouns) in self.properNouns.items():
         if not referenceKey in history and len(nouns & words) > 0:
            history.add(referenceKey)
            return int(referenceKey)

      return None
