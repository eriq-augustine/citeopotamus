import re

import util
import parser

class Paper:
   # |parseStructire| is assumed to be a dict generated from parser::parseFullDataset().
   def __init__(self, parseStructure, root = True):
      self.root = root

      if root:
         meta = parseStructure['root']['meta']
      else:
         meta = parseStructure['meta']

      self.title = meta['title']
      self.authors = meta['authors']
      self.terms = meta['terms']
      self.categories = meta['categories']
      self.abstract = meta['abstract']

      if root:
         self.fullText = parseStructure['root']['fullText']
         self.pdfPath = parseStructure['root']['pdfPath']
      else:
         self.fullText = parseStructure['fullText']
         self.pdfPath = parseStructure['pdfPath']

      if root:
         self.noCitationsText = parseStructure['root']['noCitationsText']
         self.noNumbersText = parseStructure['root']['noNumbersText']
         self.citationKey = parseStructure['root']['citationKey']
         self.citations = parseStructure['root']['citations']

         # Do pre-processing on the citations.
         for citation in self.citations:
            # proper nouns
            citation.sentenceProperNouns = util.removeStopwords(util.getCapitalWords(citation.sentenceContext.noCitations))
            citation.paragraphProperNouns = util.removeStopwords(util.getCapitalWords(citation.paragraphContext.noCitations))

            # bigrams
            citation.sentenceBigrams = util.getNonStopNgrams(citation.sentenceContext.noCitations, 2)
            citation.paragraphBigrams = util.getNonStopNgrams(citation.paragraphContext.noCitations, 2)

            # Add important unigrams to the proper nouns
            citation.sentenceProperNouns.update(util.importantUnigrams(citation.sentenceBigrams))
            citation.paragraphProperNouns.update(util.importantUnigrams(citation.paragraphBigrams))

         # This is a dict to accomodate missing references, and index by 1.
         self.references = {}
         for reference in parseStructure['references'].items():
            self.references[reference[0]] = Paper(reference[1], False)

   def __repr__(self):
      return self.__str__()

   def __str__(self):
      rtn = '"{0}" by {1}'.format(self.title, self.authors)

      if self.root:
         rtn += "\n{0} Citations and {1} References".format(len(self.citations), len(self.references))

      return rtn

# Some context surrounding a citation.
class Context:
   # TODO(eriq): Have a good way of generating a context given just some raw text.
   # It is non-trivial to do it nocely because we need to know what cite we are on
   #  (since there can be multiple cites per context).
   def __init__(self, rawText, noCitations, noNumbers, marked, number):
      self.raw = rawText
      self.noCitations = noCitations
      self.noNumbers = noNumbers
      self.marked = marked
      self.numCitations = number

class Citation:
   def __init__(self,
                paragraph, noCitesParagraph, noNumbersParagraph, markedParagraph,
                sentence, noCitesSentence, noNumbersSentence, markedSentence,
                citesPerParagraph, citesPerSentence):
      self.sentenceContext = Context(sentence, noCitesSentence, noNumbersSentence,
                                     markedSentence, citesPerSentence)
      self.paragraphContext = Context(paragraph, noCitesParagraph, noNumbersParagraph,
                                     markedParagraph, citesPerParagraph)

      # Figure out the pre context
      self.preContext = ''
      # Check for a para surround first.
      match = re.search('\(([^\)]*{}[^\(]*)\)'.format(re.escape(parser.MARKED_CITATION_MARKER)), markedSentence)
      if match:
         self.preContext = match.group(1).replace(parser.MARKED_CITATION_MARKER, ' ').strip()
      else:
         match = re.search('([^\[\]\.,;:!"\?\-]+){}'.format(re.escape(parser.MARKED_CITATION_MARKER)), markedSentence)

         if match:
            self.preContext = match.group(1).strip()

      self.preContextUnigrams = util.getNonStopNgrams(self.preContext, 1)
      self.preContextBigrams = util.getNonStopNgrams(self.preContext, 2)
