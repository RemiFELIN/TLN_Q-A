import nltk
from nltk import CFG

### IMPORT DU FICHIER QUESTION ET UTILISATION NLTK
PATH_FILE = "D:\Travail\MIAGE\M2 MIAGE\TLN\TALN CM3+TP3\questions.xml"

file = open(PATH_FILE, "r")

def ie_preprocess(doc):
    sentences = nltk.sent_tokenize(doc)
    sentences = [nltk.word_tokenize(sent) for sent in sentences]
    sentences = [nltk.pos_tag(sent) for sent in sentences]
    return sentences

for raw in file:
    test = ie_preprocess(raw)
    print(test)