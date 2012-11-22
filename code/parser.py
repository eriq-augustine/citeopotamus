import os
import re
import sys

from paper import Paper

# Use a more complicated marker for citations to reduce chance of collisions.
CITATION_MARKER = '[<?>]'
# This is used when there are multiple citation in a context.
# This will mark the citation you are currently looking at.
MARKED_CITATION_MARKER = '[<X>]'

def parseMeta(fileName):
   fileObj = open(fileName, 'r')

   rtn = {}
   rtn['title'] = fileObj.readline().replace('TITLE: ', '').strip()
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

   rtn['abstract'] = abstract

   return rtn

# Parse a single dir (non-recursicve)
# meta.txt must be present.
# paper.pdf and paper.txt may be present.
def parseDir(dirName):
   entry = {}
   entry['meta'] = parseMeta(dirName + '/meta.txt')

   if os.path.exists(dirName + '/paper.txt'):
      fileObj = open(dirName + '/paper.txt')
      entry['fullText'] = fileObj.read().strip()
   else:
      entry['fullText'] = ''

   if os.path.exists(dirName + '/paper.pdf'):
      entry['pdfPath'] = dirName + '/paper.pdf'
   else:
      entry['pdfPath'] = ''

   return entry

# This is the all purpose citation removeing method.
# |entry| is assumed to be a entry that was created with parseDir().
# It MUST HAVE 'fullText'.
# 'noNumbersText', 'noCitationsText', 'citations', and 'citationKey' fields will be added to |entry|.
# 'citations' will be a randomized list of contexts for the citations.
# 'citationKey' will be an array of citations in the order that they appear in the text.
# Both 'noNumbersText' and 'noCitationsText' will not contain anything in or after after the references section.
# NOTE: This will probably not be effective if it is not one paragraph per line.
def parseCitations(entry):
   noNumbersText = ''
   noCitationsText = ''
   citations = []
   citationKey = []
   # For when we see the references
   noMoreCitations = False

   # First, make a global replacement for multiple cites eg. '[1, 2]'
   parsedText = entry['fullText']
   groupedCitations = re.findall('\[\s*\d+\s*(?:,\s*\d+\s*)+\]', parsedText)
   for cite in groupedCitations:
      numbers = re.findall('\d+', cite)
      replacement = ''
      for number in numbers:
         replacement += '[{0}]'.format(number)
      parsedText = parsedText.replace(cite, replacement)

   # Go line by line.
   for line in parsedText.splitlines():
      rawLine = line.strip()

      if re.search('REFERENCES', rawLine):
         noMoreCitations = True

      if not noMoreCitations and re.search('\[\s*\d+\s*\]', rawLine):
         cites = re.findall('\[\s*\d+\s*\]', rawLine)

         noCitationsLine = re.sub('\[\s*\d+\s*\]', '', rawLine)
         noNumbersLine = re.sub('\[\s*\d+\s*\]', CITATION_MARKER, rawLine)

         noCitationsText += noCitationsLine + "\n"
         noNumbersText += noNumbersLine + "\n"

         for cite in cites:
            citeNum = int(re.search('(\d+)', cite).group(1))
            citationKey.append(citeNum)

            markedLine = rawLine.replace(cite, MARKED_CITATION_MARKER)
            markedLine = re.sub('\[\s*\d+\s*\]', CITATION_MARKER, markedLine)

            #TODO(eriq): Sentence.
            citations.append({'paragraph': rawLine,
                              'noCitesParagraph': noCitationsLine,
                              'noNumbersParagraph': noNumbersLine,
                              'markedParagraph': markedLine,
                              'numberOfCitesInParagraph': len(cites)
                             })
      else:
         noCitationsText += rawLine + "\n"
         noNumbersText += rawLine + "\n"

   entry['noCitationsText'] = noCitationsText
   entry['noNumbersText'] = noNumbersText
   entry['citationKey'] = citationKey
   entry['citations'] = citations


# Parse an entire directory structure.
# At the root should be the base paper, and then references/ should contain all the reference papers.
def parseFullDataset(baseDir):
   rtn = {}

   rtn['root'] = parseDir(baseDir)
   rtn['references'] = {}

   for fileName in os.listdir(baseDir + "/references"):
      rtn['references'][int(fileName)] = parseDir(baseDir + "/references/" + fileName)

   parseCitations(rtn['root'])

   return Paper(rtn)

if __name__ == "__main__":
   #print parseDir('data/dynamo')
   paper = parseFullDataset('data/dynamo')
   #parseFullDataset('data/dynamo')

   print paper
   print paper.references
