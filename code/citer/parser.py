import os
import re
import sys

import util

from paper import Paper
from paper import Citation

# Use a more complicated marker for citations to reduce chance of collisions.
CITATION_MARKER = '[<?>]'
# This is used when there are multiple citation in a context.
# This will mark the citation you are currently looking at.
MARKED_CITATION_MARKER = '[<X>]'

def parseMeta(fileName):
   fileObj = open(fileName, 'r')

   rtn = {}
   rtn['title'] = util.normalize(fileObj.readline().replace('TITLE: ', '').strip())
   rtn['authors'] = [ util.normalize(author.strip()) for author in fileObj.readline().replace('AUTHORS: ', '').split(',') ]
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
      entry['fullText'] = util.normalize(fileObj.read().strip())
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
def parseCitations(entry, references):
   noNumbersText = ''
   noCitationsText = ''
   citations = []
   citationKey = []
   # For when we see the references
   noMoreCitations = False

   referenceCount = 0

   parsedText = entry['fullText']

   # First, make a global replacement for multiple cites eg. '[1, 2]' => '[1][2]'
   groupedCitations = re.findall('\[\s*\d+\s*(?:,\s*\d+\s*)+\]', parsedText)
   for cite in groupedCitations:
      numbers = re.findall('\d+', cite)
      replacement = ''
      for number in numbers:
         replacement += '[{0}]'.format(number)
      parsedText = parsedText.replace(cite, replacement)

   # Expand citation ranges.
   # [1]-[5] => [1][2][3][4][5]
   ranges = re.findall('\[\s*\d+\s*\]\s*\-\s*\[\s*\d+\s*\]', parsedText)
   for citeRange in ranges:
      numbers = re.findall('\d+', citeRange)
      if len(numbers) != 2:
         print "WARNING: A range of non-two length was found (" + citeRange + "). No replacement will occur."
         continue

      replacement = ''
      for number in range(int(numbers[0]), int(numbers[1]) + 1):
         replacement += '[{0}]'.format(number)
      parsedText = parsedText.replace(citeRange, replacement)

   # Go line by line.
   for line in parsedText.splitlines():
      rawLine = line.strip()

      if re.search('REFERENCES', rawLine):
         noMoreCitations = True
         currentReference = 0
         continue

      if noMoreCitations:
         # In references.
         currentReference += 1

         match = re.match('\[\s*(\d+)\s*\]\s*(.*)', rawLine)
         if not match:
            print "ERROR: could not parse reference"
            return None

         if int(match.group(1)) != currentReference:
            print "ERROR: reference does not match position"
            return None

         if not references.has_key(int(match.group(1))):
            continue

         # Verify that all the authors are present.
         reference = match.group(2).upper().strip()
         authors = [ author.upper().strip() for author in re.findall('\w{3,}', ' '.join(references[currentReference]['meta']['authors'])) ]

         # Remove incorrect references
         for author in authors:
            if not author in reference:
               #print "ERROR: Author not found in reference: {}, ({})".format(author, reference)
               #TEST
               #return None
               references.pop(currentReference)
               break

         referenceCount += 1

      if not noMoreCitations and re.search('\[\s*\d+\s*\]', rawLine):
         cites = re.findall('\[\s*\d+\s*\]', rawLine)

         noCitationsLine = re.sub('\[\s*\d+\s*\]', '', rawLine)
         noNumbersLine = re.sub('\[\s*\d+\s*\]', CITATION_MARKER, rawLine)

         noCitationsText += noCitationsLine + "\n"
         noNumbersText += noNumbersLine + "\n"

         for cite in cites:
            citeNum = int(re.search('(\d+)', cite).group(1))

            markedLine = rawLine.replace(cite, MARKED_CITATION_MARKER)
            markedLine = re.sub('\[\s*\d+\s*\]', CITATION_MARKER, markedLine)

            # HACK(eriq): I am replacing anoying false-positive sentence enders eg.
            # 'e.g.', 'mr.', etc.
            # This may accidentally join extra sentences, but it is better than too short sentences.
            # This could be done in one, but it looks ugly and it should be fine.
            hackLine = re.sub(r'\be\.?g\.', '_eg_', rawLine, flags=re.IGNORECASE)
            #hackLine = re.sub(r'\bi\.?e\.', '_ie_', rawLine, flags=re.IGNORECASE)
            hackLine = re.sub(r'\bdr\.', '_dr_', hackLine, flags=re.IGNORECASE)
            hackLine = re.sub(r'\bmr\.', '_mr_', hackLine, flags=re.IGNORECASE)
            hackLine = re.sub(r'\bmrs\.', '_mrs_', hackLine, flags=re.IGNORECASE)
            hackLine = re.sub(r'\bms\.', '_ms_', hackLine, flags=re.IGNORECASE)
            hackLine = re.sub(r'\bmme\.', '_mme_', hackLine, flags=re.IGNORECASE)
            hackLine = re.sub(r'\bet\.', '_et_', hackLine, flags=re.IGNORECASE)
            hackLine = re.sub(r'\bal\.', '_al_', hackLine, flags=re.IGNORECASE)
            hackLine = re.sub(r'\b(\d+)\.(\d+)', '_\1_\2_', hackLine, flags=re.IGNORECASE)

            rawSentence = re.search(
                  '(?:^|[\.\?!])\s*([^\.\?!]*' +
                     re.escape(cite) +
                     '\s*[^\.\?!]*\s*(?:$|[\.\?!]))',
                  hackLine).group(1)

            noCitationsSentence = re.sub('\[\s*\d+\s*\]', '', rawSentence)
            noNumbersSentence = re.sub('\[\s*\d+\s*\]', CITATION_MARKER, rawSentence)
            markedSentence = rawSentence.replace(cite, MARKED_CITATION_MARKER)
            markedSentence = re.sub('\[\s*\d+\s*\]', CITATION_MARKER, markedSentence)
            citesPerSentence = len(re.findall('\[\s*\d+\s*\]', rawSentence))

            # Allow all cites in the sentence that are not seperated by a word character to be
            # allowed as a correct citation.
            # So things like [1][2][3] and [1],[2],[3] can be caught
            correctCitations = set([citeNum])
            match = re.search('(?:\[\s*\d+\s*\]\W*)*{}(?:\w*\[\s*\d+\s*\])*'.format(re.escape(cite)), rawSentence)
            if match and match.group(0) != cite:
               adjacentCites = re.findall('\[\s*\d+\s*\]', match.group(0))
               for adjacentCite in adjacentCites:
                  correctCitations.add(int(re.search('(\d+)', adjacentCite).group(1)))
            citationKey.append({'main': citeNum, 'allowed': correctCitations})

            citations.append(Citation(rawLine, noCitationsLine,
                                      noNumbersLine, markedLine,
                                      rawSentence, noCitationsSentence,
                                      noNumbersSentence, markedSentence,
                                      len(cites), citesPerSentence))
      else:
         noCitationsText += rawLine + "\n"
         noNumbersText += rawLine + "\n"

   entry['noCitationsText'] = noCitationsText
   entry['noNumbersText'] = noNumbersText
   entry['citationKey'] = citationKey
   entry['citations'] = citations

   if len(references) == 0:
      print "ERROR: Paper does not have any references"
      return None

   return True
   #TEST
   #if referenceCount != 0:
   #   print referenceCount
   #return referenceCount == 0


# Parse an entire directory structure.
# At the root should be the base paper, and then references/ should contain all the reference papers.
def parseFullDataset(baseDir):
   rtn = {}

   rtn['root'] = parseDir(baseDir)
   rtn['references'] = {}

   for fileName in os.listdir(baseDir + "/references"):
      rtn['references'][int(fileName)] = parseDir(baseDir + "/references/" + fileName)

   if parseCitations(rtn['root'], rtn['references']):
      return Paper(rtn)

   return None

if __name__ == "__main__":
   #print parseDir('data/dynamo')
   paper = parseFullDataset('data/dynamo')
   #parseFullDataset('data/dynamo')

   print paper
   print paper.references
