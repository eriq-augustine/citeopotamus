import re

import util

# The general class for algorithms that try and solve for citations.
# The hope is that every algorithm extends Method in the same pattern
# and then they can be switched out.
# Utility methods (perhaps a special split string or stopword removal) should probably go in here.
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

         titleNouns = re.findall('\w{2,}', reference.title)
         self.properNouns[key] |= set([noun.upper() for noun in titleNouns])

      self.properNouns = util.uniqueSets(self.properNouns)

   def guess(self, cite, paper):
      words = util.getCapitalWords(cite.sentenceContext.noCitations)

      for (referenceKey, nouns) in self.properNouns.items():
         if len(nouns & words) > 0:
            return int(referenceKey)

      return None
