import nltk
from nltk.chunk import conlltags2tree, tree2conlltags
from pprint import pprint
import re

# iob_tagged = tree2conlltags(cs)
# pprint(iob_tagged)

### IMPORT DU FICHIER QUESTION ET UTILISATION NLTK
PATH_FILE = "questions.xml"

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

def find_question_word(text):
    text = text.lower()
    tokens = nltk.word_tokenize(text)    
    question_keyword = ['where', 'when', 'who', 'how', 'whom', 'in which', 'what is', 'which']
    for i, word in enumerate(tokens):
        print(word, i)
        for word in question_keyword:
            if word in question_keyword:
                answer = word
            else: answer = None
    if answer == 'where':
        print('the answer will be a place')
    elif answer == 'when':
        print('the answer will be a date')
    elif answer == 'who':
        print('the answer will be a person or a company/firm')
    elif answer == 'how':
        print('the answer will be a quantity (number) or a NC')
    elif answer == 'whom':
        print('the answer will be a person')
    elif answer == 'in which':
        print('the answer will be a place')
    elif answer == 'what is':
        print('the answer can be a place or a person or a number')
    elif answer == 'which':
        print('the answer will be find with the end of the question')
    else:
        print('We dont recognize the question word')
    return answer

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
    ans = find_question_word(question)
    print(ans)

