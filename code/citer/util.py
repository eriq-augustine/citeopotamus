import re

from nltk.stem.porter import PorterStemmer

class StupidStemmer:
   def stem(self, word):
      return re.sub('[Ss]$', '', word)

#STEMMER = PorterStemmer()
STEMMER = StupidStemmer()

# Note: It convention for this code base to represent a unigram (and therefore
# n-grams) as all capital.

# Given some bigrams, find the unigrams that occur >= 25% of the time.
def importantUnigrams(bigrams):
   unigrams = set()

   counts = {}
   for bigram in bigrams:
      for word in bigram.split('-'):
         word = STEMMER.stem(word)
         if not counts.has_key(word):
            counts[word] = 1
         else:
            counts[word] += 1
   for (word, count) in counts.items():
      if float(count) / len(bigrams) >= 0.25:
         unigrams.add(word)

   return unigrams

# Given a dict of sets, return a new dict of matching sets where each item
# is unique to that set.
# n is the number of sets that a word is allowed to belong in.
def uniqueSets(sets, n = 1):
   rtn = {}

   if (n == 1):
      for currentKey in sets.keys():
         currentSet = set(sets[currentKey])

         for key in sets.keys():
            if (key != currentKey):
               currentSet -= sets[key]

         rtn[currentKey] = currentSet
   else:
      for currentKey in sets.keys():
         counts = {}

         for key in sets.keys():
            if (key != currentKey):
               words = sets[currentKey] - sets[key]
               for word in words:
                  if not counts.has_key(word):
                     counts[word] = 1
                  else:
                     counts[word] += 1

         finalWords = set()
         for (word, count) in counts.items():
            if len(sets) - count <= n:
               finalWords.add(word)
         rtn[currentKey] = finalWords


   return rtn

# TODO(eriq): Watch the first capital.
# This really aims to get proper nouns.
# Numbers count!
def getCapitalWords(text):
   words = re.findall('(?<![a-z])(?:(?:[A-Z]\w+)|\d+)', text)
   return set([word.upper() for word in words])

# This will split the text into a list (NOT SET) of unigrams.
def wordSplit(text, stem = False):
   modText = text.upper()
   modText = re.sub('\[|\]|\(|\)|,|\.|:|;|"|~|\/|\\|(--)|#|!|\?|\-', ' ', modText)
   modText = re.sub("'|\$", '', modText)
   if stem:
      return [ STEMMER.stem(word) for word in modText.split() ]
   else:
      return modText.split()

# Get n-grams, but remove stopwords before the combination.
def getNonStopNgrams(text, n):
   words = wordSplit(text)
   validWords = removeStopwords(set(words))

   bigrams = set()
   for i in range(n - 1, len(words)):
      valid = True
      gram = ''

      for j in reversed(range(0, n)):
         if not words[i - j] in validWords:
            valid = False
            break
         gram += words[i - j] + '-'

      if valid:
         bigrams.add(re.sub('\-$', '', gram))

   return bigrams

# TODO: More title stopwords
# There are more words that are considered stopwords in the context of CS acedemic Paper titles.
def removeTitleStopwords(words):
   return words - STOPWORDS - ADDITIONAL_STOPWORDS - TITLE_STOPWORDS

def removeStopwords(words):
   return words - STOPWORDS - ADDITIONAL_STOPWORDS

TITLE_STOPWORDS = set([
                       'SYSTEM',
                       'SYSTEMS',
                      ])

# These are additional stopwords that are not typically considered stopwords,
#  but are in our context.
ADDITIONAL_STOPWORDS = set([
                            'WHEN',
                            'EACH',
                            'DATA',
                            'RESULTS'
                           ])

# This list was taken from http://www.lextek.com/manuals/onix/stopwords1.html
STOPWORDS = set([
                  'A',
                  'ABOUT',
                  'ABOVE',
                  'ACROSS',
                  'AFTER',
                  'AGAIN',
                  'AGAINST',
                  'ALL',
                  'ALMOST',
                  'ALONE',
                  'ALONG',
                  'ALREADY',
                  'ALSO',
                  'ALTHOUGH',
                  'ALWAYS',
                  'AMONG',
                  'AN',
                  'AND',
                  'ANOTHER',
                  'ANY',
                  'ANYBODY',
                  'ANYONE',
                  'ANYTHING',
                  'ANYWHERE',
                  'ARE',
                  'AREA',
                  'AREAS',
                  'AROUND',
                  'AS',
                  'ASK',
                  'ASKED',
                  'ASKING',
                  'ASKS',
                  'AT',
                  'AWAY',
                  'B',
                  'BACK',
                  'BACKED',
                  'BACKING',
                  'BACKS',
                  'BE',
                  'BECAME',
                  'BECAUSE',
                  'BECOME',
                  'BECOMES',
                  'BEEN',
                  'BEFORE',
                  'BEGAN',
                  'BEHIND',
                  'BEING',
                  'BEINGS',
                  'BEST',
                  'BETTER',
                  'BETWEEN',
                  'BIG',
                  'BOTH',
                  'BUT',
                  'BY',
                  'C',
                  'CAME',
                  'CAN',
                  'CANNOT',
                  'CASE',
                  'CASES',
                  'CERTAIN',
                  'CERTAINLY',
                  'CLEAR',
                  'CLEARLY',
                  'COME',
                  'COULD',
                  'D',
                  'DID',
                  'DIFFER',
                  'DIFFERENT',
                  'DIFFERENTLY',
                  'DO',
                  'DOES',
                  'DONE',
                  'DOWN',
                  'DOWN',
                  'DOWNED',
                  'DOWNING',
                  'DOWNS',
                  'DURING',
                  'E',
                  'EACH',
                  'EARLY',
                  'EITHER',
                  'END',
                  'ENDED',
                  'ENDING',
                  'ENDS',
                  'ENOUGH',
                  'EVEN',
                  'EVENLY',
                  'EVER',
                  'EVERY',
                  'EVERYBODY',
                  'EVERYONE',
                  'EVERYTHING',
                  'EVERYWHERE',
                  'F',
                  'FACE',
                  'FACES',
                  'FACT',
                  'FACTS',
                  'FAR',
                  'FELT',
                  'FEW',
                  'FIND',
                  'FINDS',
                  'FIRST',
                  'FOR',
                  'FOUR',
                  'FROM',
                  'FULL',
                  'FULLY',
                  'FURTHER',
                  'FURTHERED',
                  'FURTHERING',
                  'FURTHERS',
                  'G',
                  'GAVE',
                  'GENERAL',
                  'GENERALLY',
                  'GET',
                  'GETS',
                  'GIVE',
                  'GIVEN',
                  'GIVES',
                  'GO',
                  'GOING',
                  'GOOD',
                  'GOODS',
                  'GOT',
                  'GREAT',
                  'GREATER',
                  'GREATEST',
                  'GROUP',
                  'GROUPED',
                  'GROUPING',
                  'GROUPS',
                  'H',
                  'HAD',
                  'HAS',
                  'HAVE',
                  'HAVING',
                  'HE',
                  'HER',
                  'HERE',
                  'HERSELF',
                  'HIGH',
                  'HIGH',
                  'HIGH',
                  'HIGHER',
                  'HIGHEST',
                  'HIM',
                  'HIMSELF',
                  'HIS',
                  'HOW',
                  'HOWEVER',
                  'I',
                  'IF',
                  'IMPORTANT',
                  'IN',
                  'INTEREST',
                  'INTERESTED',
                  'INTERESTING',
                  'INTERESTS',
                  'INTO',
                  'IS',
                  'IT',
                  'ITS',
                  'ITSELF',
                  'J',
                  'JUST',
                  'K',
                  'KEEP',
                  'KEEPS',
                  'KIND',
                  'KNEW',
                  'KNOW',
                  'KNOWN',
                  'KNOWS',
                  'L',
                  'LARGE',
                  'LARGELY',
                  'LAST',
                  'LATER',
                  'LATEST',
                  'LEAST',
                  'LESS',
                  'LET',
                  'LETS',
                  'LIKE',
                  'LIKELY',
                  'LONG',
                  'LONGER',
                  'LONGEST',
                  'M',
                  'MADE',
                  'MAKE',
                  'MAKING',
                  'MAN',
                  'MANY',
                  'MAY',
                  'ME',
                  'MEMBER',
                  'MEMBERS',
                  'MEN',
                  'MIGHT',
                  'MORE',
                  'MOST',
                  'MOSTLY',
                  'MR',
                  'MRS',
                  'MUCH',
                  'MUST',
                  'MY',
                  'MYSELF',
                  'N',
                  'NECESSARY',
                  'NEED',
                  'NEEDED',
                  'NEEDING',
                  'NEEDS',
                  'NEVER',
                  'NEW',
                  'NEW',
                  'NEWER',
                  'NEWEST',
                  'NEXT',
                  'NO',
                  'NOBODY',
                  'NON',
                  'NOONE',
                  'NOT',
                  'NOTHING',
                  'NOW',
                  'NOWHERE',
                  'NUMBER',
                  'NUMBERS',
                  'O',
                  'OF',
                  'OFF',
                  'OFTEN',
                  'OLD',
                  'OLDER',
                  'OLDEST',
                  'ON',
                  'ONCE',
                  'ONE',
                  'ONLY',
                  'OPEN',
                  'OPENED',
                  'OPENING',
                  'OPENS',
                  'OR',
                  'ORDER',
                  'ORDERED',
                  'ORDERING',
                  'ORDERS',
                  'OTHER',
                  'OTHERS',
                  'OUR',
                  'OUT',
                  'OVER',
                  'P',
                  'PART',
                  'PARTED',
                  'PARTING',
                  'PARTS',
                  'PER',
                  'PERHAPS',
                  'PLACE',
                  'PLACES',
                  'POINT',
                  'POINTED',
                  'POINTING',
                  'POINTS',
                  'POSSIBLE',
                  'PRESENT',
                  'PRESENTED',
                  'PRESENTING',
                  'PRESENTS',
                  'PROBLEM',
                  'PROBLEMS',
                  'PUT',
                  'PUTS',
                  'Q',
                  'QUITE',
                  'R',
                  'RATHER',
                  'REALLY',
                  'RIGHT',
                  'RIGHT',
                  'ROOM',
                  'ROOMS',
                  'S',
                  'SAID',
                  'SAME',
                  'SAW',
                  'SAY',
                  'SAYS',
                  'SECOND',
                  'SECONDS',
                  'SEE',
                  'SEEM',
                  'SEEMED',
                  'SEEMING',
                  'SEEMS',
                  'SEES',
                  'SEVERAL',
                  'SHALL',
                  'SHE',
                  'SHOULD',
                  'SHOW',
                  'SHOWED',
                  'SHOWING',
                  'SHOWS',
                  'SIDE',
                  'SIDES',
                  'SINCE',
                  'SMALL',
                  'SMALLER',
                  'SMALLEST',
                  'SO',
                  'SOME',
                  'SOMEBODY',
                  'SOMEONE',
                  'SOMETHING',
                  'SOMEWHERE',
                  'STATE',
                  'STATES',
                  'STILL',
                  'STILL',
                  'SUCH',
                  'SURE',
                  'T',
                  'TAKE',
                  'TAKEN',
                  'THAN',
                  'THAT',
                  'THE',
                  'THEIR',
                  'THEM',
                  'THEN',
                  'THERE',
                  'THEREFORE',
                  'THESE',
                  'THEY',
                  'THING',
                  'THINGS',
                  'THINK',
                  'THINKS',
                  'THIS',
                  'THOSE',
                  'THOUGH',
                  'THOUGHT',
                  'THOUGHTS',
                  'THREE',
                  'THROUGH',
                  'THUS',
                  'TO',
                  'TODAY',
                  'TOGETHER',
                  'TOO',
                  'TOOK',
                  'TOWARD',
                  'TURN',
                  'TURNED',
                  'TURNING',
                  'TURNS',
                  'TWO',
                  'U',
                  'UNDER',
                  'UNTIL',
                  'UP',
                  'UPON',
                  'US',
                  'USE',
                  'USED',
                  'USES',
                  'V',
                  'VERY',
                  'W',
                  'WANT',
                  'WANTED',
                  'WANTING',
                  'WANTS',
                  'WAS',
                  'WAY',
                  'WAYS',
                  'WE',
                  'WELL',
                  'WELLS',
                  'WENT',
                  'WERE',
                  'WHAT',
                  'WHEN',
                  'WHERE',
                  'WHETHER',
                  'WHICH',
                  'WHILE',
                  'WHO',
                  'WHOLE',
                  'WHOSE',
                  'WHY',
                  'WILL',
                  'WITH',
                  'WITHIN',
                  'WITHOUT',
                  'WORK',
                  'WORKED',
                  'WORKING',
                  'WORKS',
                  'WOULD',
                  'X',
                  'Y',
                  'YEAR',
                  'YEARS',
                  'YET',
                  'YOU',
                  'YOUNG',
                  'YOUNGER',
                  'YOUNGEST',
                  'YOUR',
                  'YOURS',
                  'Z',
                  ])
