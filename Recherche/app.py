from flask import Flask, render_template, request, jsonify
import plotly.express as px
import plotly.io as pio
import mysql.connector

app = Flask(__name__)

# Configuration de la base de données
db_config = {
    'host': 'localhost',
    'user': 'root',
    'database': 'scrapping_db',
    'port': 3306
}

# Fonction de recherche de produit
def recherche_produit(nom_produit):
    connexion = mysql.connector.connect(**db_config)
    curseur = connexion.cursor()

    requete = """
    SELECT produits.*, prix.prix, prix.date_prix
    FROM produits
    LEFT JOIN prix ON produits.id_produit = prix.id_produit
    WHERE produits.nom LIKE %s
    AND DATE(prix.date_prix) = CURDATE()
    AND NOT (produits.nom LIKE 'V.F%');
    """

    # Exécuter la requête avec le nom du produit en tant que paramètre
    curseur.execute(requete, (f'%{nom_produit}%',))

    # Récupérer tous les résultats
    resultats = curseur.fetchall()

    # Fermer le curseur et la connexion
    curseur.close()
    connexion.close()

    return resultats

# Fonction pour se connecter à la base de données
def connect_db():
    return mysql.connector.connect(**db_config)

# Fonction pour récupérer les données de prix depuis la base de données
def get_price_data(product_name):
    connection = connect_db()
    cursor = connection.cursor(dictionary=True)

    # Exécuter la requête SQL pour récupérer les données
    query = '''
        SELECT prix.date_prix, prix.prix, produits.nom_site
        FROM prix
        JOIN produits ON prix.id_produit = produits.id_produit
        WHERE produits.nom = %s
        ORDER BY prix.date_prix
    '''

    cursor.execute(query, (product_name,))
    data = cursor.fetchall()

    cursor.close()
    connection.close()

    return data

# Fonction pour obtenir des suggestions basées sur le préfixe
def get_suggestions(prefix):
    connexion = mysql.connector.connect(**db_config)
    curseur = connexion.cursor()

    requete = """
    SELECT DISTINCT produits.nom
    FROM produits
    WHERE produits.nom LIKE %s
    AND NOT (produits.nom LIKE 'V.F%')
    LIMIT 5;
    """

    # Exécuter la requête avec le préfixe en tant que paramètre
    curseur.execute(requete, (f'{prefix}%',))

    # Récupérer tous les résultats
    suggestions = [result[0] for result in curseur.fetchall()]

    # Fermer le curseur et la connexion
    curseur.close()
    connexion.close()

    return suggestions

# Route for search
@app.route('/Recherche', methods=['GET', 'POST'])
def search_index():
    if request.method == 'POST':
        nom_produit_recherche = request.form['nom_produit']
        resultats = recherche_produit(nom_produit_recherche)
        return render_template('resultats.html', resultats=resultats, product_name=nom_produit_recherche)

    return render_template('index.html')

# New route for visualization
@app.route('/VoirVisualisation/<product_name>', methods=['GET', 'POST'])
def voir_visualisation(product_name):
    error_message = None

    if request.method == 'POST':
        # Handle POST requests
        # Add the logic for handling POST requests here if needed
        pass
    elif request.method == 'GET':
        # Handle GET requests
        data = get_price_data(product_name)

        if not data:
            error_message = "Aucune donnée trouvée."
            return render_template('visWeb.html', graph_html=None, product_name=product_name, error_message=error_message)

        # Créer le graphique avec Plotly (scatter plot)
        fig = px.scatter(data, x='date_prix', y='prix', color='nom_site', title=f'Évolution du prix pour le produit {product_name} au fil de temps ')

        # Convertir le graphique en HTML
        graph_html = pio.to_html(fig, full_html=False)

        # Renvoyer la page HTML avec le graphique incorporé et le formulaire
        return render_template('visWeb.html', graph_html=graph_html, product_name=product_name, error_message=error_message)

    # Si la méthode n'est ni GET ni POST, renvoyer une erreur
    return "Method not allowed"

# Nouvelle route pour les suggestions
@app.route('/suggest/<prefix>', methods=['GET'])
def suggest(prefix):
    suggestions = get_suggestions(prefix)
    return jsonify(suggestions)

if __name__ == '__main__':
    app.run(debug=True)
