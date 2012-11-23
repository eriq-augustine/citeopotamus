import re

# Given a dict of sets, return a new dict of matching sets where each item
# is unique to that set.
def uniqueSets(sets):
   rtn = {}

   for currentKey in sets.keys():
      currentSet = set(sets[currentKey])

      for key in sets.keys():
         if (key != currentKey):
            currentSet -= sets[key]
            
      rtn[currentKey] = currentSet

   return rtn

# TODO(eriq): Watch the first capital.
def getCapitalWords(text):
   words = re.findall('(?<![a-z])[A-Z]\w+', text)
   return set([word.upper() for word in words])
