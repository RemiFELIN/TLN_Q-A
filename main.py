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
# On cherche les requetes
pattern_request = re.compile(r'"en">(Give\s[A-Za-z\s]*\.)')


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


def find_key_word(text):
    for elem in text:
        elem = str(elem)
        elem = elem.lower()
        # what is -> what / in which -> in == pour éviter les erreurs de lecture
        keyword = ['where', 'when', 'who', 'how', 'whom', 'in', 'what', 'which', 'give']
        for q in keyword:
            if elem.find(q) != -1:
                return q
    return None


def print_rule(answer):
    if answer == 'where':
        print(answer, ': the answer will be a place')
    elif answer == 'when':
        print(answer, ': the answer will be a date')
    elif answer == 'who':
        print(answer, ': the answer will be a person or a company/firm')
    elif answer == 'how':
        print(answer, ': the answer will be a quantity (number) or a NC')
    elif answer == 'whom':
        print(answer, ': the answer will be a person')
    elif answer == 'in':
        print(answer, ': the answer will be a place')
    elif answer == 'what':
        print(answer, ': the answer can be a place or a person or a number')
    elif answer == 'which':
        print(answer, ': the answer will be find with the end of the question')
    elif answer == "give":
        print(answer, ": it is a request !")
    else:
        print(answer, ': We dont recognize the question word')
    print()
    return answer


# To find question and request
for raw in file:
    question = pattern_question.findall(raw)
    request = pattern_request.findall(raw)
    if len(question) != 0:
        questions.append(question)
    elif len(request) != 0:
        questions.append(request)

# We will analyze it
for question in questions:
    # cast list in string to do preprocess
    question = ''.join(question)
    line = ie_preprocess(question)
    line = ner(line)
    print("--------------------------------")
    print(">", question)
    print(line)
    print_rule(find_key_word(line))

