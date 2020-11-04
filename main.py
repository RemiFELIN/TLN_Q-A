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
import requests
from nltk.metrics import *
from nltk.corpus import wordnet
import lxml.etree as etree

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

# Utile pour tester (service dbpedia lookup temporairement
# indisponible (erreur 503))
str_test = "<ArrayOfResult>\
	<Result>\
		<Label>\
		<URI>http://dbpedia.org/resource/Brooklyn_Bridge</URI>\
		<Description>\
			Lorem Ipsum\
		</Description>\
		</Label>\
	</Result>\
</ArrayOfResult>"


# Tokenizer and pos_tag
def ie_preprocess(doc):
    return nltk.pos_tag(nltk.word_tokenize(doc))


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


def lookup(keyword):
    """
    Using DBpedia Lookup for keywords
    :return:
    True si la ressource a été trouvé dans la base
    False sinon
    None si une erreur est rencontré (voir log associé)
    """
    url = "https://lookup.dbpedia.org/api/search.asmx/KeywordSearch?"
    try:
        query_string = str(keyword)
        query_string = query_string.replace(" ", "_")
        post_params = {
            'QueryString': query_string
        }
        data = urllib.parse.urlencode(post_params).encode('UTF-8')
        url += str(data.decode())
        # todo
        # get retourne une erreur 503
        # on test donc avec notre variable de test pour la suite du
        # développement

        # get = requests.get(url)
        get = str_test
        root = fromstring(get)
        if root[0] is not None:
            # Nous avons des résultats pour la ressource trouvée par le NER
            # On retourne le dernier mot du endpoint pour etre sur de prendre
            # une clé conforme pour nos requêtes
            s = re.compile(r'resource/([A-za-z]*)')
            return (s.findall(root[0][0][0].text))[0]
        print("[WARN] lookup: no result found")
        return None
    except ValueError:
        print("[ERROR] lookup: error format -> expected : '<class 'str'>'\
         / given : '{}'".format(type(keyword)))
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


def build_query(key, input, mod):
    # On test si pour la clé donnée, la ressource est disponible sur dbpedia
    # On utilise ainsi 'lookup' (un service de dbpedia)
    if lookup(key) is not None:
        key = lookup(key)
        # Catch SynthaxWarning
        warnings.filterwarnings("ignore")
        # Use SPARQL Wrapper
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        prefix = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX dbp: <http://dbpedia.org/property/> " \
                 "PREFIX res: <http://dbpedia.org/resource/> "
        select = "SELECT DISTINCT ?uri "
        f = None
        if mod == "dbo":
            f = "WHERE { res:" + key + " dbo:" + input + " ?uri . }"
        elif mod == "dbp":
            f = "WHERE { res:" + key + " dbp:" + input + " ?uri . }"
        else:
            print("[ERROR] build_query: 'mod'={} is not avalaible / expected : 'dbo' or 'dbp'".format(mod))
        query = str(prefix + select + f)
        sparql.setQuery(query)
        sparql.setReturnFormat(XML)
        result = sparql.query().convert()
        return result
    elif lookup(key) is False:
        print("[WARN] build_query: Aucune ressource trouvé pour key={}".format(key))
    else:
        print("[ERROR] build_query: lookup('{}') is", lookup(key))


def choose_response(response):
    # Read and map xml in root
    results = []
    root = fromstring(response.toxml())
    for i in range(len(root[1])):
        results.append(root[1][i][0][0].text)
    print(results)
    '''
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
    # For each element in redquest_in_text
    for elem in request_in_text:
        # cast response in Text nltk
        tokens = nltk.word_tokenize(elem)
        text = nltk.Text(tokens)
        print(text)
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
    '''
    return results


# To find question and request
for raw in file:
    question = pattern_question.findall(raw)
    request = pattern_request.findall(raw)
    if len(question) != 0:
        questions.append(question)
    elif len(request) != 0:
        questions.append(request)

# We will analyze it
i = 1
reponses_given = 0
for question in questions:
    # cast list in string to do preprocess
    question = ''.join(question)
    print("--------------------------------")
    print(i, ">", question)
    line = ner(question)
    print("ner:", line)
    # print("preprocess:", ie_preprocess(question))
    # lookup("Brooklyn Bridge")
    try:
        if lookup(line[0][0]) is not None:
            # todo : à modifier avec le mot clé
            #  (pour l'instant 1 bonne réponse seulement)
            entitie = lookup(line[0][0])
            res = build_query(entitie, "crosses", "dbo")
            reponses = choose_response(res)
            if reponses is None:
                reponses = "TODO -> choose good keyword !"
                reponses_given += 1
    except IndexError:
        print("Aucun NER trouvé !")
    responses_from_system.append(reponses)
    print(i, "> Réponse:", reponse)
    i += 1

    # for ent, lab in line:
    # print("> Entité trouvé : '{}' qui est du type {}".format(ent, lab))
    # print("> rule(s):", get_rule(find_key_word(ie_preprocess(question))))

# print(">>> TEST DE QUERY")
# res = build_request(build_query("Brooklyn_Bridge", "crosses"))
# print(choose_response(read_xml(res), None))

###################################################################################
print("\n>>> EVALUATION DU SYSTEME\n")


# Calcul des métriques
def Recall(reponses_given_by_system, standard_answer):
    recall = reponses_given_by_system / standard_answer
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
print("recall : {}".format(Recall(reponses_given, len(questions))))
print("precision: {} soit {}%".format(Precision(score, len(responses_from_file)),
                                      round(Precision(score, len(responses_from_file)) * 100, 2)))
print("F-measure: {}".format(
    F_measure(Precision(score, len(responses_from_file)), Recall(reponses_given, len(responses_from_file)))))

# print(">>> TEST SYNSET")
# for synomys in wordnet.synsets("mayor"):
# for l in synomys.lemmas():
# print(l.name())
