import method
import parser
import sys

def main():
   #paper = parser.parseFullDataset('data/dynamo')
   paperName = '../data/A Bayesian Inference Framework to Reconstruct Transmission Trees Using Epidemiological and Genetic Data'
   if len(sys.argv) > 1:
      paperName = sys.argv[1]
   paper = parser.parseFullDataset(paperName)
   print paper

   debugRun(paper)

def debugRun(paper):
   methods = []
   methods.append(method.TitleAuthorMethod(paper))
   methods.append(method.SentenceContextAbstractBigramsMethod(paper))
   methods.append(method.SentenceContextAbstractWordsMethod(paper))
   methods.append(method.ParagraphContextAbstractBigramsMethod(paper))
   methods.append(method.ParagraphContextAbstractWordsMethod(paper))

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
