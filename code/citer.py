import method
import parser

def main():
   paper = parser.parseFullDataset('data/dynamo')
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

      print '---------'
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

   print "{0} / {1}".format(hits, len(paper.citations))

if __name__ == "__main__":
   main()
