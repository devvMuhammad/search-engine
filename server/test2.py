from nltk import WordNetLemmatizer, pos_tag, word_tokenize
from nltk.corpus import wordnet

lem = WordNetLemmatizer()
while True: 
  word = input("Enter word:\t")

  # Get the single character pos constant from pos_tag like this:
  pos_label = (pos_tag(word_tokenize(word))[0][1][0]).lower()

  # pos_refs = {'n': ['NN', 'NNS', 'NNP', 'NNPS'],
  #            'v': ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'],
  #            'r': ['RB', 'RBR', 'RBS'],
  #            'a': ['JJ', 'JJR', 'JJS']}

  # print 10 closest synonyms
  if pos_label == 'j': pos_label = 'a'    # 'j' <--> 'a' reassignment
  print(pos_label)
  if pos_label in ['r']:  # For adverbs it's a bit different
      print(lem.lemmatize(word, 'r'))
      if(wordnet.synsets(word+'.r')):
        print(wordnet.synset(word+'.r.1').lemmas()[0].pertainyms()[0].name())
  elif pos_label in ['a', 's', 'v']: # For adjectives and verbs
      print(lem.lemmatize(word))
  else:   # For nouns and everything else as it is the default kwarg
      print(lem.lemmatize(word))