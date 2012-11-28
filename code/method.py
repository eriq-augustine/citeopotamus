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

class AbstractMethod(Method):
   def __init__(self, paper):
      self.abstractWords = {}
      self.abstractBigrams = {}

      for (key, reference) in paper.references.items():
         self.abstractWords[key] = util.getCapitalWords(reference.abstract)
         #self.abstractWords[key] = util.removeStopwords(set(util.wordSplit(reference.abstract)))
         self.abstractBigrams[key] = util.getNonStopNgrams(reference.abstract, 2)

      self.abstractWords = util.uniqueSets(self.abstractWords)
      self.abstractBigrams = util.uniqueSets(self.abstractBigrams)

      # If a word appears in >= 25% of bigrams, then put it in the unigrams.
      for (referenceKey, bigrams) in self.abstractBigrams.items():
         counts = {}
         for bigram in bigrams:
            for word in bigram.split('-'):
               word = util.STEMMER.stem(word)
               if not counts.has_key(word):
                  counts[word] = 1
               else:
                  counts[word] += 1
         for (word, count) in counts.items():
            if float(count) / len(bigrams) >= 0.25:
               self.abstractWords[referenceKey].add(word)

      #TEST
      print "ABSTRACT:"
      for (ref, nouns) in self.abstractWords.items():
         print "{0}\n\tWords -- {1}\n\tBigrams -- {2}".format(ref, nouns, self.abstractBigrams[ref])

      # There will be no more than one citation per reference per context (probably).
      self.contextHistory = {}

   def guess(self, cite, paper):
      words = util.removeStopwords(util.getCapitalWords(cite.paragraphContext.noCitations))
      bigrams = util.getNonStopNgrams(cite.paragraphContext.noCitations, 2)

      # Get the citation history for this context
      if not self.contextHistory.has_key(cite.paragraphContext.noCitations):
         self.contextHistory[cite.paragraphContext.noCitations] = set()
      history = self.contextHistory[cite.paragraphContext.noCitations]

      maxIntersection = 0
      bestRef = None

      # If a word appears in >= 25% of bigrams, then put it in the unigrams.
      counts = {}
      for bigram in bigrams:
         for word in bigram.split('-'):
            word = util.STEMMER.stem(word)
            if not counts.has_key(word):
               counts[word] = 1
            else:
               counts[word] += 1
      for (word, count) in counts.items():
         if float(count) / len(bigrams) >= 0.25:
            words.add(word)

      #TEST
      print bigrams
      print words

      # Check the bigrams first.
      for (referenceKey, abstractBigrams) in self.abstractBigrams.items():
         if not referenceKey in history:
            intersection = len(abstractBigrams & bigrams)
            if intersection > maxIntersection:
               maxIntersection = intersection
               bestRef = referenceKey

      if bestRef:
         history.add(bestRef)
         return int(bestRef)

      for (referenceKey, nouns) in self.abstractWords.items():
         if not referenceKey in history:
            intersection = len(nouns & words)
            if intersection > maxIntersection:
               maxIntersection = intersection
               bestRef = referenceKey

      if bestRef:
         history.add(bestRef)
         return int(bestRef)

      return None
