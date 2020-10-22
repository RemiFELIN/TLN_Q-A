import nltk
from nltk.chunk import conlltags2tree, tree2conlltags
from pprint import pprint
import spacy
from spacy import displacy
import en_core_web_sm
import re
import urllib
from SPARQLWrapper import SPARQLWrapper, XML
from xml.etree.ElementTree import XML, fromstring
import xml.etree.ElementTree as ET
import sys
import io
import warnings
from nltk.metrics import *

# IMPORT DU FICHIER QUESTION ET UTILISATION NLTK
PATH_FILE = "questions.xml"

file = open(PATH_FILE, "r")
line = ""

# On cherche les questions :
questions = []
pattern_question = re.compile(r'"en">([A-Za-z.\s]*\?)')
# On cherche les requetes
pattern_request = re.compile(r'"en">(Give\s[A-Za-z\s]*\.)')

# On va stocker les réponses de notre système
responses_from_system = []


# Tokenizer and pos_tag
def ie_preprocess(doc):
    sent = nltk.word_tokenize(doc)
    sent = nltk.pos_tag(sent)
    return sent


# NER with Spacy
nlp = spacy.load('en_core_web_sm')


def ner(l):
    entities = []
    ner_nlp = nlp(l)
    for e in ner_nlp.ents:
        entities.append([e.text, e.label_])
    return entities


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


def get_rule(answer):
    # return a type of response for our requests
    if answer == 'where':
        # print(answer, ': the answer will be a place')
        return ["place"]
    elif answer == 'when':
        # print(answer, ': the answer will be a date')
        return ["date"]
    elif answer == 'who':
        # print(answer, ': the answer will be a person or a company/firm')
        return ["person", "company", "firm"]
    elif answer == 'how':
        # print(answer, ': the answer will be a quantity (number) or a NC')
        return ["number", "NC"]
    elif answer == 'whom':
        # print(answer, ': the answer will be a person')
        return ["person"]
    elif answer == 'in':
        # print(answer, ': the answer will be a place')
        return ["place"]
    elif answer == 'what':
        # print(answer, ': the answer can be a place or a person or a number')
        return ["person", "number"]
    elif answer == 'which':
        # print(answer, ': the answer will be find with the end of the question')
        return ["person", "company", "firm"]
    elif answer == "give":
        # print(answer, ": it is a request !")
        return ["list"]
    else:
        print(answer, ': We dont recognize the question word')
        return None


def build_query(key, input):
    liste = []
    simil = []
    prefix = " PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX res: <http://dbpedia.org/resource/> "
    select = "SELECT DISTINCT ?uri "
    # with open("relations.txt", "r") as a_file:
    #     for line in a_file:
    #         stripped_line = line.strip()
    #         liste.append(stripped_line)
    # for i in liste:
    #     edit_distance(i, verb)
    filter = "WHERE { res:" + key + " dbo:" + input + " ?uri . }"
    query = str(prefix + select + filter)
    return query


# Building query (SPARQL Request)
def build_request(query):
    # Catch SynthaxWarning
    warnings.filterwarnings("ignore")
    # Use SPARQL Wrapper
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(XML)
    result = sparql.query().convert()
    return result


def read_xml(result):
    results = []
    root = fromstring(result.toxml())
    for i in range(len(root[1])):
        results.append(root[1][i][0][0].text)
    return results


def choose_response(response, tag):
    if tag is None and len(response) != 0:
        # return first link
        return response[0]
    elif len(response) != 0:
        # 0 Result so return None
        return None
    response_choosen = None
    # Replace pounctuation (.:/#) by space
    request_in_text = []
    for i in range(len(response)):
        text = response[i].replace(".", " ")
        text = text.replace("/", " ")
        text = text.replace(":", " ")
        text = text.replace("#", " ")
        request_in_text.append(text)
    # For each element in request_in_text
    for elem in request_in_text:
        # cast response in Text nltk
        tokens = nltk.word_tokenize(elem)
        text = nltk.Text(tokens)
        # A method to redirect print value into a variable
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout
        # Our matcher
        text.similar(tag)
        output = new_stdout.getvalue()
        sys.stdout = old_stdout
        # We choose first one which match
        if output != "No matches":
            response_choosen = response[request_in_text.index(elem)]
            break
    return response_choosen


# To find question and request
for raw in file:
    print(raw)
    question = pattern_question.findall(raw)
    request = pattern_request.findall(raw)
    if len(question) != 0:
        questions.append(question)
        print(question)
    elif len(request) != 0:
        print(request)
        questions.append(request)

# We will analyze it
i = 1
for question in questions:
    # cast list in string to do preprocess
    question = ''.join(question)
    print("--------------------------------")
    print(i, ">", question)
    line = ner(question)
    entitie = None
    reponse = "TODO -> entité non trouvé"
    for ent, lab in line:
        entitie = ent
    if entitie is not None:
        # todo : à modifier avec le mot clé
        #  (pour l'instant 1 bonne réponse seulement)
        # entitie format to catch QueryBadFormed
        entitie = entitie.replace(" ", "_")
        res = build_request(build_query(entitie, "crosses"))
        reponse = choose_response(read_xml(res), None)
        if reponse is None:
            reponse = "TODO -> choose good keyword !"
    responses_from_system.append(reponse)
    print(i, "> Réponse:", reponse)
    i += 1

    # for ent, lab in line:
    # print("> Entité trouvé : '{}' qui est du type {}".format(ent, lab))
    # print("> rule(s):", get_rule(find_key_word(ie_preprocess(question))))

# print(">>> TEST DE QUERY")
# res = build_request(build_query("Brooklyn_Bridge", "crosses"))
# print(choose_response(read_xml(res), None))


print("\n>>> EVALUATION DU SYSTEME")


# Calcul des métriques
def Recall(our_correct_answer, standard_answer):
    recall = our_correct_answer / standard_answer
    return recall


def Precision(our_correct_answer, number_answer):
    precision = our_correct_answer / number_answer
    return precision


def F_measure(precision, recall):
    num = 2 * precision * recall
    den = precision + recall
    f_measure = num / den
    return f_measure


# reponses du fichier
responses_from_file = []

# Lecture des réponses du fichier
file_to_xml = ET.parse(PATH_FILE)
root = file_to_xml.getroot()
# Pour chaques questions
for i in range(len(root)):
    tag = root[i][-1].tag
    reponses = []
    if tag == "answers":
        for answer in root[i][-1]:
            reponses.append(answer[0].text)
        responses_from_file.append(reponses)
    else:
        reponses.append("TO_FIND")
        responses_from_file.append(reponses)

# Calcul des paramètres
score = 0
# test pour voir si on a pas fait d'erreur
if len(responses_from_file) == len(responses_from_system):
    for i in range(len(responses_from_file)):
        for response in responses_from_file[i]:
            if responses_from_system[i] == response:
                score += 1
else:
    print("[ERROR] len(responses_system) ({}) != len(responses_file) ({})".format(len(responses_from_system),
                                                                                  len(responses_from_file)))

### LOG
print("score : {}/{}".format(score, len(responses_from_file)))
print("precision: {}%".format(Precision(score, len(responses_from_file))))
print("F-measure: {}".format(
    F_measure(Precision(score, len(responses_from_file)), Recall(score, len(responses_from_file)))))
