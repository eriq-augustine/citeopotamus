import operator
import os
import sys

from constants import DEBUG

import method
import parser

DATA_DIR = '../data'

AVAILABLE_METHODS = [
                     method.PreContextTitleAuthorMethod,
                     method.SentenceTitleAuthorMethod,
                     method.PreContextAbstractWordsMethod,
                     method.SentenceContextAbstractBigramsMethod,
                     method.PreContextAbstractBigramsMethod,
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
   allHitRefs = set()
   allRefs = set()

   for paperName in os.listdir(DATA_DIR):
      paper = None

      try:
         paper = parser.parseFullDataset(DATA_DIR + '/' + paperName)
         paperRes = normalRun(paper)

         allHitRefs.update(paperRes[2])
         allRefs.update([ ref.title.strip().upper() for ref in paper.references.values()])

         res.append((paperRes[0], paperRes[1]))
      except OSError:
         print "Error parsing paper: " + paperName
         continue

   res = sorted(res, reverse = True)
   total = 0
   for paper in res:
      print paper[1]
      total += paper[0]
   print "Total Papers: {}".format(len(res))
   print "Average: {}".format(total / len(res))
   if len(res) % 2 == 0:
      print "Median: {}".format((res[len(res) / 2][0] + res[len(res) / 2 - 1][0]) / 2.0)
   else:
      print "Median: {}".format(res[len(res) / 2][0])

   print "Hit Refs: {}, All Refs: {}".format(len(allHitRefs), len(allRefs))
   print "Foaad Metric: {}".format(float(len(allHitRefs)) / len(allRefs))

def normalRun(paper):
   methods = [ method(paper) for method in AVAILABLE_METHODS ]

   hits = 0
   misses = 0
   # Don't count references without any information
   total = 0

   # foaad counting system
   hitRefs = set()

   for i in range(0, len(paper.citations)):
      cite = paper.citations[i]
      correctReference = paper.citationKey[i]

      # Skip citations that do not have a reference.
      if not paper.references.has_key(correctReference['main']):
         continue

      total += 1

      # Don't count if a value is unreported (earlier phases of the pipeline do not report).
      # But make sure to only count a hit once.
      reportedValue = False
      for methodObj in methods:
         guess = methodObj.guess(cite, paper)
         if guess:
            if guess in correctReference['allowed']:
               hits += 1
               hitRefs.add(paper.references[guess].title.strip().upper())
            else:
               misses += 1
            break

   return ((float(hits) / total),
           "{:.2%}\t(Hits: {},\tMisses: {},\tTotal: {})\t{}".format((float(hits) / total), hits, misses, total, paper.title),
           hitRefs)

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
         if not paper.references.has_key(correctReference['main']):
            continue

         guess = methodObj.guess(cite, paper)
         if guess in correctReference['allowed']:
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
      if not paper.references.has_key(correctReference['main']):
         print "Warning: There is no citation information found for citation #{}, skipping".format(correctReference['main'])
         continue

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
            if guess in correctReference['allowed']:
               hits += 1
            else:
               misses += 1

      print res
      print "Actual Reference: {0}".format(correctReference['allowed'])
      print '---------'

   print "HITS: {0} / {1} ({2})".format(hits, len(paper.citations), hits / float(len(paper.citations)))
   print "Misses: {0}".format(misses)

if __name__ == "__main__":
   main()
