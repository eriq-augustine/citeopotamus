import operator
import os
import sys

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
   # full test mode
   if '-f' in sys.argv:
      fullTest()
      return

   #paper = parser.parseFullDataset('data/dynamo')
   #paperName = '../data/A Bayesian Inference Framework to Reconstruct Transmission Trees Using Epidemiological and Genetic Data'
   paperName = '../data/A Graphical Modelling Approach to the Dissection of Highly Correlated Transcription Factor Binding Site Profiles'
   if '-p' in sys.argv:
      paperName = sys.argv[sys.argv.index('-p') + 1]
   paper = parser.parseFullDataset(paperName)
   print paper

   # Ordering mode
   if '-o' in sys.argv:
      orderingRun(paper)
   else:
      debugRun(paper)

def fullTest():
   res = []
   for paperName in os.listdir('../data'):
      paper = None

      try:
         paper = parser.parseFullDataset('../data/' + paperName)
         res.append(normalRun(paper))
      except OSError:
         print "Error parsing paper: " + paperName
         next

   res = sorted(res, reverse = True)
   for paper in res:
      print paper[1]

def normalRun(paper):
   methods = [ method(paper) for method in AVAILABLE_METHODS ]

   hits = 0
   misses = 0
   # Don't count references without any information
   total = 0

   for i in range(0, len(paper.citations)):
      cite = paper.citations[i]
      correctReference = paper.citationKey[i]

      # Skip citations that do not have a reference.
      if not paper.references.has_key(correctReference):
         next

      total += 1

      # Don't count if a value is unreported (earlier phases of the pipeline do not report).
      # But make sure to only count a hit once.
      reportedValue = False
      for methodObj in methods:
         guess = methodObj.guess(cite, paper)
         if guess:
            if guess == correctReference:
               hits += 1
            else:
               misses += 1
            break

   #print "{} (Hits: {}, Misses: {}, Total: {}) -- {}".format((float(hits) / total), hits, misses, total, paper.title)
   #print "{:.2%}\t(Hits: {},\tMisses: {},\tTotal: {})\t-- {}".format((float(hits) / len(paper.citations)), hits, misses, len(paper.citations), paper.title)
   return ((float(hits) / len(paper.citations)), "{:.2%}\t(Hits: {},\tMisses: {},\tTotal: {})\t{}".format((float(hits) / len(paper.citations)), hits, misses, len(paper.citations), paper.title))


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
