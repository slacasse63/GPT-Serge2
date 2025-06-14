import os
from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)

# Connexion à Azure Blob Storage via variable d’environnement
AZURE_CONN = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONN)
container_name = "memoire-gpt-serge"  # nom du conteneur dans Azure

# Création explicite du client de conteneur (manquait dans ta version)
container_client = blob_service_client.get_container_client(container_name)

@app.route("/read", methods=["GET"])
def read_blob():
    fichier = request.args.get("fichier")
    try:
        blob_client = container_client.get_blob_client(blob=fichier)
        contenu = blob_client.download_blob().readall().decode("utf-8")
        return contenu
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

@app.route("/write", methods=["POST"])
def write_blob():
    data = request.get_json()
    fichier = data.get("fichier")
    contenu = data.get("contenu")
    try:
        blob_client = container_client.get_blob_client(blob=fichier)
        blob_client.upload_blob(contenu, overwrite=True)
        return jsonify({"message": f"Le fichier '{fichier}' a été écrit avec succès."})
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

@app.route("/list", methods=["GET"])
def lister_memoire():
    prefix = request.args.get("prefix", "")
    try:
        fichiers = []
        blobs = container_client.list_blobs(name_starts_with=prefix)
        for blob in blobs:
            fichiers.append(blob.name)
        return jsonify(fichiers)
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

if __name__ == "__main__":
    app.run()
