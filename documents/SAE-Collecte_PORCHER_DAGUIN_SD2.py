# -*- coding: utf-8 -*-
"""
Created on Thu Jan  4 20:21:26 2024
@author: leaph
@author: dagui
"""

# Importer les modules
import urllib
import bs4 
import pandas
import re
import folium
import webbrowser
import matplotlib.pyplot as plt
from jinja2 import Template
from IPython.display import HTML

# 2 fonctions pour les coordonnées géographiques - conversion
def dms2dd(degrees, minutes, seconds, direction):
    # Conversion des coordonnées DMS en décimales
    dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60);
    if direction in ('sud', 'ouest'):
        dd *= -1
    return dd

def parse_dms(dms):
    # Analyse et conversion des coordonnées DMS en décimales
    parts = re.split('[^\d\w]+', dms)
    coord = dms2dd(parts[0], parts[1], parts[2], parts[3])
    return coord

# URL de la page Wikipedia contenant les données sur les aéroports
url = "https://fr.wikipedia.org/wiki/Liste_des_a%C3%A9roports_les_plus_fr%C3%A9quent%C3%A9s_en_France"
page = urllib.request.urlopen(url).read()
html = bs4.BeautifulSoup(page, "lxml")

# Recherches des informations du tableau principal
tabAeroport = html.find('table', {'class': 'wikitable alternance sortable'})
table_body = tabAeroport.find('tbody')
lesAeroports = table_body.find_all('tr')

# Création du DataFrame pour stocker les données des aéroports
df = pandas.DataFrame(columns=['Rang_2019', 'aeroport', 'evolution22_21', 'evolution22_19', 'Voyageurs_2022', 'Voyageurs_2021', 'Voyageurs_2020', 'Voyageurs_2019', 'Voyageurs_2018', 'Voyageurs_2017', 'Voyageurs_2016', 'Voyageurs_2015', 'Voyageurs_2014', 'Voyageurs_2013', 'Voyageurs_2012', 'Voyageurs_2011', 'Voyageurs_2010', 'Voyageurs_2005', 'Voyageurs_2000', 'Latitude', 'Longitude','url'])

i = 1 

for unAeroport in lesAeroports:
    infosAeroport = unAeroport.find_all('td')
    
    # Extraction des informations de chaque colonne pour un aéroport
    listeColonnes = [uneInfo.text.strip() for uneInfo in infosAeroport]

    # Recherche de liens hypertextes dans chaque balise <a> de chaque <td> (infosAeroport)
    for uneInfo in infosAeroport:
        if uneInfo.find('a') is not None:
            # Si le nom de l'aéroport correspond à la balise <a>
            # On compare au nom de l'éaroport qui est dans listeColonnes[1] avec un split car certains noms d'aéroports contiennent des petites notes qu'il ne faut pas prendre en compte 
            if uneInfo.find('a').text.strip() == listeColonnes[1].split('[')[0].strip():
                urlDebut = uneInfo.find('a').get('href')
                urlAeroport = "http://fr.wikipedia.org" + urlDebut
                nom_aeroport = uneInfo.find('a').get('title')
                # Accès à la page de l'aéroport pour trouver ses coordonnées géographiques
                search_Aeroport = urllib.request.urlopen(urlAeroport).read()
                soup_Aeroport = bs4.BeautifulSoup(search_Aeroport, features="lxml")

                coordonnees = soup_Aeroport.find('a', {'class': "mw-kartographer-maplink"})
                if coordonnees is None :
                    latitude = ""
                    longitude = "" 
                else :
                    for uneCoordonnee in coordonnees :
                        liste = uneCoordonnee.split(",")          
                        latitude = str(liste[0]).replace(" ", "") + "'"
                        longitude = str(liste[1]).replace(" ", "") + "'"                      

    # on ajoute les informations de l'aéroport au DataFrame
    if len(listeColonnes) >= 20:
        i += 1
        # Ajout d'une ligne dans le DataFrame pour l'aéroport
        df.loc[i] = [listeColonnes[0], nom_aeroport, listeColonnes[3], listeColonnes[4], listeColonnes[5], listeColonnes[6], listeColonnes[7], listeColonnes[8], listeColonnes[9], listeColonnes[10], listeColonnes[11], listeColonnes[12], listeColonnes[13], listeColonnes[14], listeColonnes[15], listeColonnes[16], listeColonnes[17], listeColonnes[18], listeColonnes[19], latitude, longitude,urlAeroport]
        
# Conversion des coordonnées DMS en décimales pour le DataFrame
df['Latitude'] = df['Latitude'].apply(parse_dms)
df['Longitude'] = df['Longitude'].apply(parse_dms)


# Définir une fonction pour convertir les valeurs de voyageurs en 2022 en catégories
def categorize_voyageurs(val):
    val = val.replace("\xa0", "").replace(" ", "").replace(",", "")
    val = int(val)
    if val < 100000:
        return 'Moins de 100 000 voyageurs en 2022'
    elif val < 1000000:
        return 'Moins de 1 000 000 voyageurs en 2022'
    elif val < 5000000:
        return 'Moins de 5 000 000 voyageurs en 2022'
    elif val < 10000000:
        return 'Moins de 10 000 000 voyageurs en 2022'
    else:
        return 'Plus de 10 000 000 voyageurs en 2022'

# Appliquer la fonction à la colonne Voyageurs_tranche que l'on créer
df['Voyageurs_tranche'] = df['Voyageurs_2022'].apply(categorize_voyageurs)

# Définir une fonction pour assigner la couleur en fonction des catégories de voyageurs
def assign_color(val):
    colorMapping = {
        'Moins de 100 000 voyageurs en 2022': 'green',
        'Moins de 1 000 000 voyageurs en 2022': 'beige',
        'Moins de 5 000 000 voyageurs en 2022': 'orange',
        'Moins de 10 000 000 voyageurs en 2022' : 'red',
        'Plus de 10 000 000 voyageurs en 2022' : 'purple',
    }
    return colorMapping.get(val, 'gray')

# Créer une carte centrée sur Paris
CarteFrance = folium.Map(location=[48.8566, 2.3522], zoom_start=5, margin=(200,200), control_scale=True)

# Ajouter des marqueurs pour chaque aéroport avec des couleurs correspondant aux catégories de voyageurs
for index, row in df.iterrows():
    if not pandas.isnull(row['Latitude']) and not pandas.isnull(row['Longitude']):

        # Création d'un message popup pour chaque marqueur avec le nom de l'aéroport et le nombre de voyageurs en 2022
        nom_aeroport = '<a href="' + row['url'] + '" target="_blank">' + row['aeroport'] + '</a>'  # Nom de l'aéroport avec le lien
        message_popup = "<b>" + nom_aeroport + "</b></br>" + row['Voyageurs_2022']
        colorMarker = assign_color(row['Voyageurs_tranche'])  # Récupérer la couleur
        popup = folium.Popup(message_popup)
        folium.Marker([row['Latitude'], row['Longitude']], tooltip=row['aeroport'], popup=popup, icon=folium.Icon(color=colorMarker)).add_to(CarteFrance)


# Créer une légende pour les couleurs
legend_html = """
<div style="position: fixed; bottom: 10px; left: 10px; z-index: 1000; background-color: white; padding: 5px; border: 2px solid gray;">
    <h4>Légende</h4>
    <p><span style="background-color: #72B026; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></span> Moins de 100 000 voyageurs en 2022</p>
    <p><span style="background-color: #FFCB92; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></span> Moins de 1 000 000 voyageurs en 2022</p>
    <p><span style="background-color: #F69730; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></span> Moins de 5 000 000 voyageurs en 2022</p>
    <p><span style="background-color: #D63E2A; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></span> Moins de 10 000 000 voyageurs en 2022</p>
    <p><span style="background-color: #D252B9; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></span> Plus de 10 000 000 voyageurs en 2022</p>
</div>
"""

# Ajouter la légende à la carte
CarteFrance.get_root().html.add_child(folium.Element(legend_html))

# Enregistrer et ouvrir la carte
CarteFrance.save('Carte_Aeroport.html')
#webbrowser.open_new_tab("Carte_Aeroport.html")


#==============================================Graphiques=====================================================================



#------------Evolution entre 2021 et 2022 des 20 aéroports ayant eu la fréquentation la plus importante en 2022--------------

# Convertir la colonne 'Voyageurs_2022' en type numérique
df['Voyageurs_2022'] = df['Voyageurs_2022'].astype(str).str.replace('\xa0', '')
df['Voyageurs_2022'] = df['Voyageurs_2022'].astype(int)

# Suppression des caractères non numériques
df['evolution22_21'] = df['evolution22_21'].astype(str).str.replace('%', '').str.replace('\xa0', '').str.replace('−', '-').astype(float)


# Sélectionner les 20 pays avec le plus grand nombre de voyageurs en 2022
top_20_aeroport = df.nlargest(20, 'Voyageurs_2022').sort_values(by='evolution22_21', ascending=True)


# Créer le graphique en barres pour le taux d'évolution
plt.figure(figsize=(16, 8))
bars = plt.barh(top_20_aeroport['aeroport'],top_20_aeroport['evolution22_21'], color='skyblue')

plt.xlabel('Taux d\'Evolution entre 2021 et 2022 (%)')
plt.ylabel('Aéroport')

plt.title('Taux d\'Evolution des 20 Premiers aéroports en Nombre de Voyageurs entre 2021 et 2022')
plt.xticks(rotation=0)
plt.tight_layout()

# Ajouter les étiquettes de valeur sur chaque barre

for bar in bars:
    xval = bar.get_width()
    plt.text(xval, bar.get_y() + bar.get_height() / 2, f'{round(xval)}%', ha='left', va='center', color='black')

# Sauvegarde du graphique
fig = plt.gcf()
fig.savefig("voyageursEvolution22_21.png")

# Afficher le graphique
# plt.show()


#-------------Diagramme circulaire de la répartition de la fréquentations en 2022 des 5 premiers aéroports-----------------------
# Sélectionner les 5 premiers aéroports selon leur fréquentation en 2022
top_5_frequentation = df.nlargest(5, 'Voyageurs_2022')

# Créer un diagramme circulaire
plt.figure(figsize=(8, 8))

# Valeurs à représenter dans le diagramme circulaire (fréquentation)
sizes = top_5_frequentation['Voyageurs_2022']

# Couleurs pour chaque tranche du diagramme circulaire
colors = ['gold', 'yellowgreen', 'lightcoral', 'lightskyblue', 'purple']

# Création du diagramme circulaire
plt.pie(sizes, colors=colors, autopct='%1.1f%%', startangle=140)

# Aspect du diagramme circulaire (aspect ratio égal pour un cercle)
plt.axis('equal')

# Titre du diagramme circulaire
plt.title('Top 5 des Aéroports selon la Fréquentation en 2022', fontsize=20, pad=20)

# Créer une colonne 'color' dans le DataFrame top_5_frequentation pour stocker les couleurs associées à chaque aéroport
top_5_frequentation['color'] = ['gold', 'yellowgreen', 'lightcoral', 'lightskyblue', 'purple']


# Sauvegarde du graphique
fig = plt.gcf()
fig.savefig("GraphCirculaireTrop5.png")

# Affichage du diagramme circulaire
#plt.show()

#-----------------------Les 10 aéroports ayant les plus grosses fréquentations en 2022-----------------------
# Convertir la colonne 'Voyageurs_2022' en type numérique
df['Voyageurs_2022'] = df['Voyageurs_2022'].astype(str).str.replace('\xa0', '').astype(int)

# Converti la colonne 'Frequentation' en type de données numérique (int)
df['Voyageurs_2022'] = pandas.to_numeric(df['Voyageurs_2022'], errors='coerce')

# Sélectionner les 10 parcs ayant la fréquentation la plus élevée
top_10_frequentation = df.nlargest(10, 'Voyageurs_2022')

# Afficher la liste des 10 parcs avec la fréquentation la plus élevée
#print(top_10_frequentation[['aeroport', 'Voyageurs_2022']])


#==========================Tableau de bord============================

# Definie le contenue du Tableau de bord
html = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tableau de bord</title>

    <!-- Ajoutez ces liens pour DataTables -->
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.css">
    <script type="text/javascript" charset="utf8" src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.js"></script>

    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            text-align: center;
            margin: 20px 200px 20px 200px
        }
        
        h1 {
            color: darkblue;
            border: 2px solid darkblue; 
            padding: 10px; 
            display: inline-block;
        }
        
        h2 {
            color: #333;
        }

        .container {
            width: 80%;
            margin: 20px auto;
            margin-left: 50px auto;
            margin-right: 50px auto;
        }

        .section-container {
            width: 100%;
            margin-bottom: 20px;
        }

        iframe, img {
            width: 100%;
            height: 600px;
            border: none;
            margin-bottom: 20px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
            background-color: white; /* Couleur de fond blanche */
        }

        th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <h1>Tableau de bord des aéroports français</h1>

    <div class="container section-container">
        <h2>Carte des aéroports</h2>
        <iframe src="Carte_Aeroport.html"></iframe>
    </div>

    <div class="container section-container">
        <h2>Evolution de la fréquentation entre 2021 et 2022</h2>
        <img src="voyageursEvolution22_21.png">
    </div>
    

    <div class="container section-container">
    <h2>Répartition de la fréquentation dans les cinq premiers aéroports en 2022</h2>
        <div class="legend-container" style="background-color: white; padding: 10px; border: 1px solid #ccc; display: flex; align-items: center;">
            <img src="GraphCirculaireTrop5.png" style="width: 60%; height: auto;">
            <!-- Légende -->
            <div style="margin-left: 20px;">
                <h3 style="margin-bottom: 5px;">Légende </h3>
                <div style="font-size: 12px;">
                    {% for index in range(5) %}
                        <p style="margin-bottom: 3px; display: flex; align-items: center;">
                            <span style="background-color: {{ top_5_frequentation.iloc[index]['color'] }}; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></span>
                            <span>{{ top_5_frequentation.iloc[index]['aeroport'] }}</span>
                        </p>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <div class="container section-container">
        <h2>Top 10 des Aéroports suivant leur fréquentation en 2022</h2>
        <table class="data-table">
            <tr>
                <th style="text-align: center;">Nom des aéroports</th>
                <th style="text-align: center;">Fréquentation</th>
            </tr>
            {% for parc in top_10_aeroports %}
            <tr>
                <td>{{ parc.aeroport }}</td>
                <!-- Utilisation du séparateur d'espace pour les milliers et alignement à droite -->
                <td style="text-align: right;">{{ '{:,.0f}'.format(parc.Voyageurs_2022).replace(',', ' ') }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="team">
        <p>Ce tableau de bord vous est proposé par Léa PORCHER et Thibault DAGUIN - BUT SD2 - VCOD</p>
    </div>

    <script>
        $(document).ready(function() {
            $('.data-table').DataTable();
        });
    </script>
</body>
</html>

"""

# Créer une liste de dictionnaire pour le top 10 des parcs
top_10_aeroports = top_10_frequentation[['aeroport', 'Voyageurs_2022']].to_dict(orient='records')


# Créer un template
template = Template(html)

# Insère le top 5 des aéroports dans le template
rendered_html = template.render(top_10_aeroports=top_10_aeroports, top_5_frequentation=top_5_frequentation)

# sauvegarde l'HTML
with open("dashboard.html", "w", encoding="utf-8") as html_file:
    html_file.write(rendered_html)

# Ouvre la page HTML
webbrowser.open("dashboard.html")

# Affiche le dashboard HTML
HTML(html)
