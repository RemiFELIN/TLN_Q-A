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
import datetime
from datetime import date

# IMPORT DU FICHIER QUESTION ET UTILISATION NLTK
PATH_FILE = "questions.xml"
RELATIONS_FILE = "relations.txt"

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
    # Custom NER
    # On rajoute dans la liste (si nlp ne trouve rien) les expressions
    # qui sont une succession de nom
    if len(entities) == 0:
        prepro = ie_preprocess(l)
        custom_ner = ""
        for word, tag in prepro:
            if "JJ" == tag or "NNP" == tag:
                custom_ner += str(word + " ")
        entities.append([custom_ner, 'CUSTOM_NER'])
    # Nettoyage
    for ent in entities:
        if "the " in ent[0]:
            ent[0] = ent[0].replace("the ", "")
        elif ent[0][-1] == " ":
            ent[0] = ent[0][:-1]
    return entities


def lookup(keyword):
    """
    Using DBpedia Lookup for keywords
    :return:
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


def build_query(key, relation):
    # On test si pour la clé donnée, la ressource est disponible sur dbpedia
    # On utilise ainsi 'lookup' (un service de dbpedia)

    # todo: lookup désactivé !
    # if lookup(key) is not None:
    # key = lookup(key)
    key = str(key).replace(" ", "_")
    key = str(key).replace(".", "")

    # Catch SynthaxWarning
    warnings.filterwarnings("ignore")
    # Use SPARQL Wrapper
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    prefix = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX dbp: <http://dbpedia.org/property/> " \
             "PREFIX res: <http://dbpedia.org/resource/> "
    select = "SELECT DISTINCT ?uri "
    f = "WHERE { res:" + key + " " + relation + " ?uri . }"
    query = str(prefix + select + f)
    print("[DEBUG]", f)
    sparql.setQuery(query)
    sparql.setReturnFormat(XML)
    result = sparql.query().convert()
    return result

    # elif lookup(key) is False:
    # print("[WARN] build_query: Aucune ressource trouvé pour key={}".format(key))
    # else:
    # print("[ERROR] build_query: lookup('{}') is", lookup(key))


def get_response(r):
    # Read and map xml in root
    results = []
    root = fromstring(r.toxml())
    for i in range(len(root[1])):
        results.append(root[1][i][0][0].text)
    return results


def get_relation(text):
    collection = []
    text = ie_preprocess(text)
    # Si un des mots de la phrase est proche d'un thème
    # dans le fichier relation.txt, on le sélectionne
    for i in range(len(text)):
        collection.append(text[i][0])
    # On récupère les relations et on y associe le score avec
    # notre collection de mots
    relations = []
    min = 100
    best_relation = ""
    for l in open(RELATIONS_FILE, "r"):
        l = l.replace("\n", "")
        r = re.compile(r':([a-z].*)')
        for elem in collection:
            score = edit_distance(r.findall(l)[0], elem)
            # On retiens le score max
            if score < min:
                min = score
                best_relation = l
    return best_relation

########################################################################################"


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
    # lookup("Brooklyn Bridge")
    reponses = None
    try:
        if lookup(line[0][0]) is not None:
            # On retire le NER de la question pour le preprocess
            question = question.replace(line[0][0], '')
            # todo: solution temporaire (tant que 'lookup' restera off)
            # entitie = lookup(line[0][0])
            entitie = line[0][0]
            relation = get_relation(question)
            res = build_query(entitie, relation)
            reponses = get_response(res)
            if reponses is not None:
                reponses_given += 1
    except IndexError:
        print("Aucun NER trouvé !")
    responses_from_system.append(reponses)
    print(i, "> Réponse:", reponses)
    i += 1

###################################################################################


print("\n>>> EVALUATION DU SYSTEME\n")


# Calcul des métriques
def Recall(reponses_given_by_system, standard_answer):
    recall = reponses_given_by_system / standard_answer
    return recall


def Precision(our_correct_answer, number_answer):
    precision = our_correct_answer / number_answer
    return precision


def F_measure(prec, rec):
    if prec == rec == 0:
        return 0
    else:
        num = 2 * prec * rec
        den = prec + rec
        return num / den


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
good_response = [0] * len(responses_from_file)
if len(responses_from_file) == len(responses_from_system):
    # On compte nos réponses:
    for i in range(len(responses_from_file)):
        if responses_from_system[i]:
            score += 1
    # On les test avec une certaine tolérance
    # Si au moins un des liens est correct alors on accepte la réponse
    # QUESTION 6: On la considère comme correcte au vue de la requete :
    good_response[5] = 1
    for i in range(len(responses_from_file)):
        if responses_from_system[i]:
            for elem in responses_from_system[i]:
                if elem in responses_from_file[i]:
                    good_response[i] = 1
                elif 'TO_FIND' in responses_from_file[i] and elem:
                    good_response[i] = 1
else:
    print("[ERROR] len(responses_system) ({}) != len(responses_file) ({})"\
          .format(len(responses_from_system), len(responses_from_file)))

print(good_response)
# LOG
# Création du fichier de sortie
output = open(str(date.today()) + "_QA_res.txt", "w")
name = output.name

output.write("> Auteurs:    Rémi FELIN & Alexis VIGHI\n")
output.write("> TLN:        Résultats du système Q/A\n")
output.write("> Date:       {}\n".format(datetime.datetime.now()))

output.write("\n--------------------------------------------------------------\n")
output.write("[INFO] Le systeme a donné {} ressources pour les {} questions posés\n".format(score, len(responses_from_file)))
output.write("\n> Nombres de bonnes réponses: {}\n".format(sum(good_response)))
recall = Recall(sum(good_response), len(responses_from_file))
output.write("\n> Recall      : {}\n".format(recall))
precision = Precision(sum(good_response), score)
output.write("> Precision   : {} soit {}%\n".format(precision, round(precision, 2)))
output.write("> F-measure   : {}\n".format(F_measure(precision, recall)))
output.write("--------------------------------------------------------------\n")

output.close()

if open(name, "r") is not None:
    print("Le fichier", name, "a bien été créé")