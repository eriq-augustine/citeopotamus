import re

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
