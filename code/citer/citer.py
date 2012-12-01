import method
import parser
import sys

def main():
   #paper = parser.parseFullDataset('data/dynamo')
   paperName = 'data/Comparative Analysis of RNA Families Reveals Distinct Repertoires for Each Domain of Life'
   if len(sys.argv) > 1:
      paperName = sys.argv[1]
   paper = parser.parseFullDataset(paperName)
   print paper

   debugRun(paper)

def debugRun(paper):
   methods = []
   methods.append(method.ProperNounMethod(paper))
   methods.append(method.AbstractMethod(paper))

   hits = 0

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
      print res
      print "Actual Reference: {0}".format(correctReference)
      print '---------'

   print "{0} / {1} ({2})".format(hits, len(paper.citations), hits / float(len(paper.citations)))

if __name__ == "__main__":
   main()
