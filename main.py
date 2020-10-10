import nltk
from nltk.chunk import conlltags2tree, tree2conlltags
from pprint import pprint
import re

# iob_tagged = tree2conlltags(cs)
# pprint(iob_tagged)

### IMPORT DU FICHIER QUESTION ET UTILISATION NLTK
PATH_FILE = "D:\Travail\MIAGE\M2 MIAGE\TLN\TALN CM3+TP3\questions.xml"

file = open(PATH_FILE, "r")
line = ""

# On cherche les questions :
questions = []
pattern_question = re.compile(r'"en">([A-Za-z\s]*\?)')

# On cherche les requetes :
requests = []
pattern_request = re.compile(r'')

# Tokenizer and pos_tag
def ie_preprocess(doc):
    sent = nltk.word_tokenize(doc)
    sent = nltk.pos_tag(sent)
    return sent


# NER
def ner(l):
    pattern = 'NP: {<DT>?<JJ>*<NN>}'
    cp = nltk.RegexpParser(pattern)
    cs = cp.parse(l)
    return cs


# To find question
for raw in file:
    question = pattern_question.findall(raw)
    if len(question) != 0:
        questions.append(question)


# We will analyze it
for question in questions:
    # cast list in string to do preprocess
    question = ''.join(question)
    line = ie_preprocess(question)
    print(ner(line))

