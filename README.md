# TLN_Q-A
Conception et implémentation d’un système de questions réponses en langue naturelle sur des données structurées

## Pour le bon fonctionnement, veuillez installer les packages suivant:  
nltk    
pprint   
spacy  
en_core_web_sm  
re  
urllib  
SPARQLWrapper  
xml.etree.ElementTree  
io  
warnings  


Après les imports des libraries, nous importons les fichiers servant au bon déroulement du code.
(question.xml et relations.txt)

Après avoir ouvert le fichier et trouvé les questions, on va pouvoir commencer à faire du preprocessing sur notre fichier.
On va commencer par le tokeniser puis on va trouver les ner (name entities recognition) de nos token.

La fonction lookup est mise en standby à cause du serveur dbpedia qui est 'down'.
Néamoins, elle fonctionne de la sorte :
On va rentrer les mots clés que l'on a trouvé précedemment, qui vont être preprocessé, en remplaçant les espaces par des '_'.
On va pouvoir entrer les keywords non compatibles avec les requêtes, afin que lookup cherche les concordances et puisse trouver le keyword associé (U.S. deviendra United States par exemple)

La fonction build query est la fonction qui va permettre de créer les query en prenant les mots clés trouvés précédemment ainsi que les relations que l'on a établi entre les mots de la question et les mots du fichiers 'relations.txt'.

COmme expliqué plus haut, la fonction get_relation va permettre d'établir des liens entre les mots de la question, à l'aide de la fonction de nltk : edit-distance, et les dbo/dbp du fichier 'relations.txt'

On va calculer nos métrics, que sont le recall, precision, et le f_score.  
Enfin, nous mettons tout en commun, en 'reliant' chaque fonction afin de pouvoir lire, traiter le document, chercher les relations, donner des réponses et calculer notre score.
Ce score sera alors édité dans un fichier à part.

