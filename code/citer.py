import method
import parser

def main():
   paper = parser.parseFullDataset('data/dynamo')
   print paper

   debugRun(paper)

def debugRun(paper):
   methodObj = method.ProperNounMethod(paper)

   for cite in paper.citations:
      print '---------'
      print cite.sentenceContext.raw
      print cite.sentenceContext.marked
      print methodObj.guess(cite, paper)
      print '---------'

if __name__ == "__main__":
   main()
