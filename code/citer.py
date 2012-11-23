import parser

def main():
   paper = parser.parseFullDataset('data/dynamo')
   print paper

   for cite in paper.citations:
      print cite.sentenceContext.marked

if __name__ == "__main__":
   main()
