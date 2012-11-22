import os
import sys

def parseMeta(fileName):
   fileObj = open(fileName, 'r')

   rtn = {}
   rtn['title'] = fileObj.readline().replace('TITLE: ', '')
   rtn['authors'] = [ author.strip() for author in fileObj.readline().replace('AUTHORS: ', '').split(',') ]
   rtn['terms'] = [ term.strip() for term in fileObj.readline().replace('TERMS: ', '').split(',') ]
   rtn['categories'] = [ cat.strip() for cat in fileObj.readline().replace('CATEGORIES: ', '').split(',') ]

   # Throw away the ABSTRACT line
   fileObj.readline()
   abstract = fileObj.readline().strip()

   line = fileObj.readline()
   while (line != ''):
      abstract += " " + line
      line = fileObj.readline().strip()

   #rtn['abstract'] = abstract
   rtn['abstract'] = 'ABSTRACT'

   return rtn

# Parse a single dir (non-recursicve)
# meta.txt must be present.
# paper.pdf and paper.txt may be present.
def parseDir(dirName):
   entry = {}
   entry['meta'] = parseMeta(dirName + '/meta.txt')

   if os.path.exists(dirName + '/paper.txt'):
      fileObj = open(dirName + '/paper.txt')
      entry['fullText'] = 'TEXT'
      #entry['fullText'] = fileObj.read().strip()
   else:
      entry['fullText'] = none

   if os.path.exists(dirName + '/paper.pdf'):
      entry['pdfPath'] = dirName + '/paper.pdf'
   else:
      entry['pdfPath'] = none

   return entry


# Parse an entire directory structure.
# At the root should be the base paper, and then references/ should contain all the reference papers.
def parseFullDataset(baseDir):
   rtn = {}

   rtn['root'] = parseDir(baseDir)
   rtn['references'] = {}

   for fileName in os.listdir(baseDir + "/references"):
      rtn['references'][int(fileName)] = parseDir(baseDir + "/references/" + fileName)

   return rtn

if __name__ == "__main__":
   #print parseDir('data/dynamo')
   print parseFullDataset('data/dynamo')
