import re

import util
from constants import DEBUG

# The general class for algorithms that try and solve for citations.
# The hope is that every algorithm extends Method in the same pattern
# and then they can be switched out.
# Utility methods (perhaps a special split string or stopword removal) should probably go in here.
# WARNING: A Method may maintain state data about the citations it has done.
#  This is very important in the cases that there are multiple cites in a single context (sentence, paragraph, etc).
#  Therefore, you should only use a method instance on one citation cycle (itteration through the paper).
class Method(object):
   # Return None if you can't make a guess.
   def guess(self, cite, paper):
      return None

class ContextMethod(Method):
   def __init__(self):
      # There will be no more than one citation per reference per context (probably).
      self.contextHistory = {}

   # Get the context that the current Method uses from the reference.
   # This is assumed to be a map of {refKey: [ context grams ]}.
   def getReferenceContext(self, paper):
      print "WARNING: Base getReferenceContext() called."
      return None

   # Get the context that the current Method uses from the cite.
   # This is mainly used to resolve history issues.
   def getCiteContext(self, cite):
      print "WARNING: Base getCiteContext() called."
      return None

   # Split the context
   def getCiteContextGrams(self, cite):
      print "WARNING: Base getCiteContext() called."
      return None

   def guess(self, cite, paper):
      context = self.getCiteContext(cite)
      grams = self.getCiteContextGrams(cite)

      # Get the citation history for this context
      if not self.contextHistory.has_key(context):
         self.contextHistory[context] = set()
      history = self.contextHistory[context]

      maxIntersection = 0
      bestRef = None

      if DEBUG:
         print grams

      for (referenceKey, abstractGrams) in self.getReferenceContext(paper).items():
         if not referenceKey in history:
            intersection = len(abstractGrams & grams)
            if intersection > maxIntersection:
               maxIntersection = intersection
               bestRef = referenceKey

      if bestRef:
         history.add(bestRef)
         return int(bestRef)

      return None

# Title/Author methods

class BaseTitleAuthorMethod(ContextMethod):
   properNouns = {}

   def __init__(self, paper):
      super(BaseTitleAuthorMethod, self).__init__()

      if BaseTitleAuthorMethod.properNouns.has_key(paper.title):
         return

      # Pre-build a list of all proper nouns in the references' title and authors.
      paperProperNouns = {}

      # TODO(eriq): remove stopwords and try to remove other capitilization false positives.
      for (key, reference) in paper.references.items():
         # Make sure to avoid initials (and double initials).
         authorNouns = re.findall('\w{3,}', ' '.join(reference.authors))
         paperProperNouns[key] = set([authorNoun.upper() for authorNoun in authorNouns])
         paperProperNouns[key] |= util.removeTitleStopwords(util.getCapitalWords(reference.title))

      paperProperNouns = util.uniqueSets(paperProperNouns, 1)

      if DEBUG:
         print "Title/Author:"
         for (ref, nouns) in paperProperNouns.items():
            print "{0} -- {1}".format(ref, nouns)

      BaseTitleAuthorMethod.properNouns[paper.title] = paperProperNouns

   def getReferenceContext(self, paper):
      return BaseTitleAuthorMethod.properNouns[paper.title]

class SentenceTitleAuthorMethod(BaseTitleAuthorMethod):
   def __init__(self, paper):
      super(SentenceTitleAuthorMethod, self).__init__(paper)

   def getCiteContext(self, cite):
      return cite.sentenceContext.noCitations

   def getCiteContextGrams(self, cite):
      return cite.sentenceProperNouns

class PreContextTitleAuthorMethod(BaseTitleAuthorMethod):
   def __init__(self, paper):
      super(PreContextTitleAuthorMethod, self).__init__(paper)

   def getCiteContext(self, cite):
      return cite.sentenceContext

   def getCiteContextGrams(self, cite):
      return cite.preContextUnigrams

# ABSTRACT methods

class BaseAbstractMethod(ContextMethod):
   abstractWords = {}
   abstractBigrams = {}

   def __init__(self, paper):
      super(BaseAbstractMethod, self).__init__()

      if BaseAbstractMethod.abstractWords.has_key(paper.title):
         return

      paperAbstractWords = {}
      paperAbstractBigrams = {}

      for (key, reference) in paper.references.items():
         paperAbstractWords[key] = util.getCapitalWords(reference.abstract)
         #paperAbstractWords[key] = util.removeStopwords(set(util.wordSplit(reference.abstract)))
         paperAbstractBigrams[key] = util.getNonStopNgrams(reference.abstract, 2)

      paperAbstractWords = util.uniqueSets(paperAbstractWords)
      paperAbstractBigrams = util.uniqueSets(paperAbstractBigrams)

      # If a word appears in >= 25% of bigrams, then put it in the unigrams.
      for (referenceKey, bigrams) in paperAbstractBigrams.items():
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
               paperAbstractWords[referenceKey].add(word)

      if DEBUG:
         print "ABSTRACT:"
         for (ref, nouns) in paperAbstractWords.items():
            print "{0}\n\tWords -- {1}\n\tBigrams -- {2}".format(ref, nouns, paperAbstractBigrams[ref])

      BaseAbstractMethod.abstractWords[paper.title] = paperAbstractWords
      BaseAbstractMethod.abstractBigrams[paper.title] = paperAbstractBigrams

class PreContextAbstractWordsMethod(BaseAbstractMethod):
   def __init__(self, paper):
      super(PreContextAbstractWordsMethod, self).__init__(paper)

   def getReferenceContext(self, paper):
      return BaseAbstractMethod.abstractWords[paper.title]

   def getCiteContext(self, cite):
      return cite.sentenceContext.noCitations

   def getCiteContextGrams(self, cite):
      return cite.preContextUnigrams

class PreContextAbstractBigramsMethod(BaseAbstractMethod):
   def __init__(self, paper):
      super(PreContextAbstractBigramsMethod, self).__init__(paper)

   def getReferenceContext(self, paper):
      return BaseAbstractMethod.abstractBigrams[paper.title]

   def getCiteContext(self, cite):
      return cite.sentenceContext.noCitations

   def getCiteContextGrams(self, cite):
      return cite.preContextBigrams

class SentenceContextAbstractWordsMethod(BaseAbstractMethod):
   def __init__(self, paper):
      super(SentenceContextAbstractWordsMethod, self).__init__(paper)

   def getReferenceContext(self, paper):
      return BaseAbstractMethod.abstractWords[paper.title]

   def getCiteContext(self, cite):
      return cite.sentenceContext.noCitations

   def getCiteContextGrams(self, cite):
      return cite.sentenceProperNouns

class SentenceContextAbstractBigramsMethod(BaseAbstractMethod):
   def __init__(self, paper):
      super(SentenceContextAbstractBigramsMethod, self).__init__(paper)

   def getReferenceContext(self, paper):
      return BaseAbstractMethod.abstractBigrams[paper.title]

   def getCiteContext(self, cite):
      return cite.sentenceContext.noCitations

   def getCiteContextGrams(self, cite):
      return cite.sentenceBigrams

class ParagraphContextAbstractWordsMethod(BaseAbstractMethod):
   def __init__(self, paper):
      super(ParagraphContextAbstractWordsMethod, self).__init__(paper)

   def getReferenceContext(self, paper):
      return BaseAbstractMethod.abstractWords[paper.title]

   def getCiteContext(self, cite):
      return cite.paragraphContext.noCitations

   def getCiteContextGrams(self, cite):
      return cite.paragraphProperNouns

class ParagraphContextAbstractBigramsMethod(BaseAbstractMethod):
   def __init__(self, paper):
      super(ParagraphContextAbstractBigramsMethod, self).__init__(paper)

   def getReferenceContext(self, paper):
      return BaseAbstractMethod.abstractBigrams[paper.title]

   def getCiteContext(self, cite):
      return cite.paragraphContext.noCitations

   def getCiteContextGrams(self, cite):
      return cite.paragraphBigrams
