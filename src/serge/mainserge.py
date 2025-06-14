import os
from datetime import datetime
import pytz
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
@app.route("/meta", methods=["GET"])
def get_metadata():
    fichier = request.args.get("fichier")
    try:
        blob_client = container_client.get_blob_client(blob=fichier)
        props = blob_client.get_blob_properties()
        return jsonify({
            "fichier": fichier,
            "taille_octets": props.size,
            "taille_mo": round(props.size / 1024 / 1024, 2),
            "modifie_le": props.last_modified.strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

@app.route("/now", methods=["GET"])
def get_current_datetime():
    tz = pytz.timezone("Canada/Eastern")
    now = datetime.now(tz)
    abrev_anglaise = now.strftime("%Z")  # 'EST' ou 'EDT'
    abrevs_fr = {"EST": "HNE", "EDT": "HAE"}
    abrev_fr = abrevs_fr.get(abrev_anglaise, abrev_anglaise)

    return jsonify({
        "iso": now.astimezone(pytz.utc).isoformat(),
        "horodatage": now.strftime(f"%Y/%m/%d-%H:%M:%S {abrev_fr}"),
        "timezone": "Canada/Eastern",
        "abreviation": abrev_fr
    })

from datetime import datetime
import pytz

@app.route("/cloturer-session", methods=["POST"])
def cloturer_session():
    try:
        # Obtenir l'heure locale formatée pour nommer le dossier
        tz = pytz.timezone("Canada/Eastern")
        now = datetime.now(tz)
        timestamp = now.strftime("950-sessions/%Y-%m-%dT%H-%M-%SZ")

        source_prefix = "fmus/selac2/010-memoire/900-temporaire/"
        target_prefix = f"fmus/selac2/010-memoire/{timestamp}/"

        moved_files = []

        for blob in container_client.list_blobs(name_starts_with=source_prefix):
            source_blob = container_client.get_blob_client(blob.name)
            target_name = blob.name.replace(source_prefix, target_prefix)

            # Copier le fichier
            copied_blob = container_client.get_blob_client(target_name)
            copied_blob.start_copy_from_url(source_blob.url)

            # Supprimer le fichier d’origine
            container_client.delete_blob(blob.name)
            moved_files.append(target_name)

        return jsonify({
            "message": f"{len(moved_files)} fichier(s) déplacé(s)",
            "nouveau_dossier": target_prefix,
            "fichiers": moved_files
        })

    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

@app.route("/write-get", methods=["GET"])
def write_blob_get():
    fichier = request.args.get("fichier")
    contenu = request.args.get("contenu")
    
    if not fichier or not contenu:
        return jsonify({"erreur": "Paramètres 'fichier' et 'contenu' requis"}), 400

    try:
        blob_client = container_client.get_blob_client(blob=fichier)
        blob_client.upload_blob(contenu, overwrite=True)
        return jsonify({"message": f"Le fichier '{fichier}' a été écrit avec succès via GET."})
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500



if __name__ == "__main__":
    app.run()
