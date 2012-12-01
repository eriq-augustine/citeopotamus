import sys
import operator

from constants import DEBUG

import method
import parser

AVAILABLE_METHODS = [
                     method.PreContextTitleAuthorMethod,
                     method.SentenceTitleAuthorMethod,
                     method.SentenceContextAbstractBigramsMethod,
                     method.ParagraphContextAbstractBigramsMethod,
                     method.SentenceContextAbstractWordsMethod,
                     method.ParagraphContextAbstractWordsMethod,
                    ]

def main():
   #paper = parser.parseFullDataset('data/dynamo')
   paperName = '../data/A Bayesian Inference Framework to Reconstruct Transmission Trees Using Epidemiological and Genetic Data'
   #if len(sys.argv) > 1:
   #   paperName = sys.argv[1]
   paper = parser.parseFullDataset(paperName)
   print paper

   # Ordering mode
   if '-o' in sys.argv:
      orderingRun(paper)
   else:
      debugRun(paper)

# This one runs all the mothods in isolation and then tries to give a suggested ordering.
# Highest precision first.
def orderingRun(paper):
   methods = [ method(paper) for method in AVAILABLE_METHODS ]
   res = {}

   for methodObj in methods:
      hits = 0
      misses = 0

      for i in range(0, len(paper.citations)):
         cite = paper.citations[i]
         correctReference = paper.citationKey[i]

         # Skip citations that do not have a reference.
         if not paper.references.has_key(correctReference):
            next

         guess = methodObj.guess(cite, paper)
         if guess == correctReference:
            hits += 1
         elif guess:
            misses += 1

      print "{} -- Misses: {}".format(methodObj.__class__.__name__, misses)
      res[methodObj.__class__.__name__] = misses

   print ''
   res = sorted(res.iteritems(), key=operator.itemgetter(1))
   for (methodName, misses) in res:
      print methodName


def debugRun(paper):
   methods = [ method(paper) for method in AVAILABLE_METHODS ]

   hits = 0
   misses = 0

   for i in range(0, len(paper.citations)):
      cite = paper.citations[i]
      correctReference = paper.citationKey[i]

      # Skip citations that do not have a reference.
      if not paper.references.has_key(correctReference):
         print "Warning: There is no citation information found for citation #{}, skipping".format(correctReference)
         next

      print '---------'
      print cite.paragraphContext.raw
      print cite.sentenceContext.raw
      print cite.sentenceContext.marked
      res = ''
      # Don't count if a value is unreported (earlier phases of the pipeline do not report).
      # But make sure to only count a hit once.
      reportedValue = False
      for methodObj in methods:
         guess = methodObj.guess(cite, paper)
         res += methodObj.__class__.__name__ + "(" + str(guess) + '), '
         if not reportedValue and guess:
            reportedValue = True
            if guess == correctReference:
               hits += 1
            else:
               misses += 1

      print res
      print "Actual Reference: {0}".format(correctReference)
      print '---------'

   print "HITS: {0} / {1} ({2})".format(hits, len(paper.citations), hits / float(len(paper.citations)))
   print "Misses: {0}".format(misses)

if __name__ == "__main__":
   main()
