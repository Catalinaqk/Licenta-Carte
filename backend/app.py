# --- ACESTA ESTE app.py COMPLET ȘI CORECTAT ---

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import os
import requests
import json

# 1. INIȚIALIZARE ȘI CONFIGURARE
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# CONFIGURARE BAZĂ DE DATE
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Opel2807*@localhost:5432/licenta_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CONFIGURARE JWT
app.config['JWT_SECRET_KEY'] = 'alot' # Cheia ta secretă JWT

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# 2. MODELELE BAZEI DE DATE
class Utilizator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    parola_hash = db.Column(db.String(60), nullable=False)

    def __init__(self, email, parola):
        self.email = email
        self.parola_hash = bcrypt.generate_password_hash(parola).decode('utf-8')

class Carti(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_google = db.Column(db.String(100), unique=True, nullable=False)
    titlu = db.Column(db.String(255), nullable=False)
    autori = db.Column(db.String(255))
    url_coperta = db.Column(db.String(500))
    descriere = db.Column(db.Text, nullable=True)  # Descriere din Google Books
    rezumat_ai = db.Column(db.Text, nullable=True)  # Rezumat generat de AI
    serie_nume = db.Column(db.String(255), nullable=True)
    serie_volum = db.Column(db.String(50), nullable=True)

    # --- CORECȚIE AICI: Am adăugat serie_nume și serie_volum în __init__ ---
    def __init__(self, id_google, titlu, autori, url_coperta, serie_nume=None, serie_volum=None, descriere=None):
        self.id_google = id_google
        self.titlu = titlu
        self.autori = autori
        self.url_coperta = url_coperta
        self.serie_nume = serie_nume
        self.serie_volum = serie_volum
        self.descriere = descriere

class Raft(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_utilizator = db.Column(db.Integer, db.ForeignKey('utilizator.id'), nullable=False)
    id_carte = db.Column(db.Integer, db.ForeignKey('carti.id'), nullable=False)
    status = db.Column(db.String(50), default='de_citit')

    def __init__(self, id_utilizator, id_carte, status='de_citit'):
        self.id_utilizator = id_utilizator
        self.id_carte = id_carte
        self.status = status

with app.app_context():
    db.create_all()

# 3. RUTELE API
@app.route("/api/test")
def test_api():
    return jsonify({"message": "Salut de la Backend-ul Python! 🐍"})

# --- Rute de Autentificare ---
@app.route("/api/register", methods=['POST'])
def register_user():
    data = request.get_json()
    email = data.get('email')
    parola = data.get('parola')
    if not email or not parola:
        return jsonify({"error": "Email și parola sunt obligatorii"}), 400
    user_existent = Utilizator.query.filter_by(email=email).first()
    if user_existent:
        return jsonify({"error": "Email deja folosit"}), 409
    try:
        utilizator_nou = Utilizator(email=email, parola=parola)
        db.session.add(utilizator_nou)
        db.session.commit()
        return jsonify({"message": f"Utilizatorul {email} a fost creat!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/login", methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    parola = data.get('parola')
    if not email or not parola:
        return jsonify({"error": "Email și parola sunt obligatorii"}), 400
    utilizator = Utilizator.query.filter_by(email=email).first()
    if utilizator and bcrypt.check_password_hash(utilizator.parola_hash, parola):
        access_token = create_access_token(identity=str(utilizator.id)) # Folosim str() - corect!
        return jsonify({
            "message": "Login reușit!",
            "token": access_token,
            "email": utilizator.email
        }), 200
    else:
        return jsonify({"error": "Email sau parolă invalidă"}), 401

# --- Rute pentru Cărți și Raft ---
@app.route("/api/search")
def search_books():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Termenul de căutare 'q' lipsește"}), 400

    api_key = 'AIzaSyBLXlCEedQBK1I62TxDiuCNnN5T_glyuiE' # Cheia ta
    google_api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&key={api_key}&maxResults=10"

    try:
        response = requests.get(google_api_url)
        if response.status_code != 200:
            error_details = response.json() if response.headers.get('content-type') == 'application/json' else {"text": response.text}
            return jsonify({
                "error": f"API-ul Google Books a eșuat cu status {response.status_code}",
                "detalii": error_details, "url_apelat": google_api_url
            }), 500

        data = response.json()
        carti_gasite = []
        if 'items' in data:
            for item in data['items']:
                info = item.get('volumeInfo', {})
                carte = {
                    "id_google": item.get('id'),
                    "titlu": info.get('title', 'N/A'),
                    "autori": info.get('authors', ['N/A']),
                    "descriere": info.get('description', 'N/A'),
                    "url_coperta": info.get('imageLinks', {}).get('thumbnail', '')
                }
                carti_gasite.append(carte)
        return jsonify(carti_gasite), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Eroare de rețea la apelarea Google Books API: {e}"}), 500

@app.route("/api/raft", methods=['GET'])
@jwt_required()
def get_raft():
    try:
        identity = get_jwt_identity()
        id_utilizator_curent = int(identity)
    except Exception as e:
        print(f"❌ Eroare la parsarea JWT (GET /raft): {str(e)}")
        return jsonify({"error": f"Eroare JWT: {str(e)}"}), 401

    try:
        carti_pe_raft = db.session.query(Raft, Carti).join(
            Carti, Raft.id_carte == Carti.id
        ).filter(
            Raft.id_utilizator == id_utilizator_curent
        ).all()

        rezultat_json = []
        for raft_entry, carte_entry in carti_pe_raft:
            rezultat_json.append({
                "id_raft": raft_entry.id,
                "status": raft_entry.status,
                "titlu": carte_entry.titlu,
                "autori": carte_entry.autori,
                "url_coperta": carte_entry.url_coperta,
                "id_google": carte_entry.id_google,
                 # Adăugăm info serie
                "serie_nume": carte_entry.serie_nume,
                "serie_volum": carte_entry.serie_volum
            })
        print(f"📚 Returnez {len(rezultat_json)} cărți pentru user {id_utilizator_curent}")
        return jsonify(rezultat_json), 200
    except Exception as e:
        print(f"❌ Eroare la citirea raftului: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/raft", methods=['POST'])
@jwt_required()
def add_to_raft():
    # --- ACEASTA ESTE VERSIUNEA CURĂȚATĂ ---
    try:
        identity = get_jwt_identity()
        id_utilizator_curent = int(identity)
    except Exception as e:
        print(f"❌ Eroare la parsarea JWT (POST /raft): {str(e)}")
        return jsonify({"error": f"Eroare JWT: {str(e)}"}), 401

    data = request.get_json()
    id_google = data.get('id_google')
    # Luăm datele inițiale trimise de frontend
    titlu_init = data.get('titlu', 'N/A')
    autori_init = data.get('autori', ['N/A'])
    url_coperta_init = data.get('url_coperta', '')

    if not id_google:
        return jsonify({"error": "ID-ul cărții lipsește"}), 400

    try:
        # Verificăm dacă ACEASTĂ CARTE există deja în baza noastră de date 'Carti'
        carte_existenta = Carti.query.filter_by(id_google=id_google).first()
        id_carte_locala = None
        carte_titlu_final = titlu_init # Folosim titlul inițial ca fallback

        if carte_existenta:
            # Dacă da, îi luăm ID-ul local
            id_carte_locala = carte_existenta.id
            carte_titlu_final = carte_existenta.titlu # Folosim titlul din DB
            print(f"📖 Cartea (id_google: {id_google}) există deja în DB Carti (ID local: {id_carte_locala})")
        else:
            # Dacă nu, o creăm în tabela 'Carti'
            print(f"➕ Cartea (id_google: {id_google}) nu există. Se adaugă în DB Carti...")
            # Inițializăm variabilele
            titlu = titlu_init
            autori = ', '.join(autori_init)
            url_coperta = url_coperta_init
            serie_nume_extras = None
            serie_volum_extras = None

            # Facem un apel la Google Books API PENTRU DETALII SUPLIMENTARE (inclusiv serie)
            api_key_books = 'AIzaSyBLXlCEedQBK1I62TxDiuCNnN5T_glyuiE' # Cheia ta
            detalii_url = f"https://www.googleapis.com/books/v1/volumes/{id_google}?key={api_key_books}"
            try:
                detalii_response = requests.get(detalii_url)
                if detalii_response.status_code == 200:
                    detalii_data = detalii_response.json()
                    volume_info = detalii_data.get('volumeInfo', {})
                    # Actualizăm datele cu cele mai precise de la Google
                    titlu = volume_info.get('title', titlu)
                    autori_list = volume_info.get('authors', [])
                    autori = ', '.join(autori_list) if autori_list else autori
                    url_coperta = volume_info.get('imageLinks', {}).get('thumbnail', url_coperta)

                    # Extragem seria, dacă există
                    series_info = volume_info.get('seriesInfo', {}).get('bookSeries', [])
                    if series_info:
                        # Google Books API: structura e [{ "seriesId": "...", "seriesBookType": "..." }]
                        first_series = series_info[0]
                        # "seriesId" conține de obicei numele seriei (ex: "Harry Potter")
                        serie_nume_extras = first_series.get('seriesId', None)
                        # "memberNumber" sau "orderNumber" ar trebui să fie volumul
                        serie_volum_extras = first_series.get('memberNumber') or first_series.get('orderNumber')
                        if not serie_volum_extras:
                            # Încercăm să extragem din titlu dacă e format "Seria Name, Vol X"
                            if serie_nume_extras and ',' in serie_nume_extras:
                                parts = serie_nume_extras.split(',')
                                serie_nume_extras = parts[0].strip()
                                if len(parts) > 1:
                                    serie_volum_extras = parts[1].strip()
                        print(f"ℹ️ Seria găsită pentru '{titlu}': {serie_nume_extras} Vol: {serie_volum_extras}")
                else:
                    print(f"⚠️ Google Books a returnat status {detalii_response.status_code} pentru detalii {id_google}")
            except Exception as e_detalii:
                print(f"⚠️ Eroare la preluarea detaliilor suplimentare pt {id_google}: {e_detalii}")

            # Creăm cartea nouă cu informațiile (posibil actualizate) despre serie
            carte_noua = Carti(
                id_google=id_google,
                titlu=titlu,
                autori=autori,
                url_coperta=url_coperta,
                serie_nume=serie_nume_extras,
                serie_volum=str(serie_volum_extras) if serie_volum_extras else None
            )
            db.session.add(carte_noua)
            db.session.commit() # Salvăm pentru a obține un ID
            id_carte_locala = carte_noua.id
            carte_titlu_final = carte_noua.titlu # Folosim titlul (posibil actualizat)
            print(f"✅ Cartea '{carte_titlu_final}' adăugată în DB Carti (ID local: {id_carte_locala})")

        # Acum avem id_carte_locala (fie existent, fie nou creat)

        # Verificăm dacă utilizatorul are DEJA cartea pe raft
        raft_existent = Raft.query.filter_by(id_utilizator=id_utilizator_curent, id_carte=id_carte_locala).first()
        if raft_existent:
            print(f"🚫 Cartea (ID local: {id_carte_locala}) este deja pe raftul userului {id_utilizator_curent}")
            return jsonify({"error": "Cartea este deja în biblioteca ta"}), 409

        # Adăugăm cartea pe raftul utilizatorului
        raft_nou = Raft(id_utilizator=id_utilizator_curent, id_carte=id_carte_locala)
        db.session.add(raft_nou)
        db.session.commit()
        print(f"➕ Cartea (ID local: {id_carte_locala}) adăugată pe raftul userului {id_utilizator_curent}")
        return jsonify({"message": f"Cartea '{carte_titlu_final}' a fost adăugată!"}), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Eroare majoră la adăugarea cărții pe raft: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/raft/<int:id_raft>", methods=['DELETE'])
@jwt_required()
def delete_from_raft(id_raft):
    try:
        identity = get_jwt_identity()
        id_utilizator_curent = int(identity)
    except Exception as e:
        print(f"❌ Eroare la parsarea JWT (DELETE /raft): {str(e)}")
        return jsonify({"error": f"Eroare JWT: {str(e)}"}), 401
    try:
        raft_entry_to_delete = Raft.query.get(id_raft)
        if not raft_entry_to_delete:
            return jsonify({"error": "Intrarea nu a fost găsită pe raft"}), 404
        if raft_entry_to_delete.id_utilizator != id_utilizator_curent:
            print(f"🚫 Tentativă de ștergere neautorizată! User: {id_utilizator_curent}, Raft Entry Owner: {raft_entry_to_delete.id_utilizator}")
            return jsonify({"error": "Nu ai permisiunea să ștergi această carte"}), 403
        db.session.delete(raft_entry_to_delete)
        db.session.commit()
        print(f"🗑️ Cartea de pe raft (ID: {id_raft}) a fost ștearsă pentru user {id_utilizator_curent}")
        return jsonify({"message": "Cartea a fost ștearsă din bibliotecă!"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Eroare la ștergerea cărții: {str(e)}")
        return jsonify({"error": str(e)}), 500

# --- Rutele AI ---
@app.route("/api/recomandari/similar", methods=['POST'])
@jwt_required()
def get_ai_recommendations():
    GEMINI_API_KEY = 'AIzaSyBLXlCEedQBK1I62TxDiuCNnN5T_glyuiE' # Cheia ta
    # Folosim combinația care a mers
    GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent?key={GEMINI_API_KEY}"

    data = request.get_json()
    titlu = data.get('titlu')
    autori = data.get('autori')
    limba = data.get('limba', 'ro')
    
    if not titlu or not autori:
        return jsonify({"error": "Titlul și autorul sunt necesare"}), 400

    # Setări limbă
    lingua_dict = {
        'ro': {
            'instruction': 'Ești un expert în literatură. Vreau să îmi recomanzi 3 cărți similare cu',
            'language_note': 'IMPORTANT: Recomandă NUMAI cărți în limba ROMÂNĂ. Titlurile și autorii trebuie să fie în limba română.',
            'format': 'Răspunde doar cu un format JSON valid, ca o listă de obiecte cu 3 chei: "titlu", "autor" și "motivare" (string scurt de ce o recomanzi).',
            'no_extra': 'Nu adăuga niciun alt text în afara JSON-ului.'
        },
        'en': {
            'instruction': 'You are a literature expert. I want you to recommend 3 books similar to',
            'language_note': 'IMPORTANT: Recommend ONLY books originally written in ENGLISH or well-known English translations. Book titles and author names must be in English.',
            'format': 'Reply only with valid JSON format, as a list of objects with 3 keys: "titlu", "autor" and "motivare" (short string why you recommend it).',
            'no_extra': 'Do not add any other text outside the JSON.'
        }
    }

    lang_config = lingua_dict.get(limba, lingua_dict['ro'])

    prompt_text = (
        f"{lang_config['instruction']} '{titlu}' de {autori}. "
        f"{lang_config['language_note']} "
        f"{lang_config['format']} "
        f"{lang_config['no_extra']}"
    )
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}

    try:
        response = requests.post(GEMINI_API_URL, json=payload, headers={'Content-Type': 'application/json'})
        if response.status_code != 200:
            error_details = response.json() if response.headers.get('content-type') == 'application/json' else {"text": response.text}
            print(f"❌ Eroare de la API-ul AI (similar): {response.status_code} - {error_details}")
            return jsonify({
                "error": f"API-ul Google AI a eșuat cu status {response.status_code}",
                "detalii": error_details, "url_apelat": GEMINI_API_URL
            }), 500

        ai_data = response.json()
        # Verificare suplimentară pentru răspuns gol sau blocat
        if 'candidates' not in ai_data or not ai_data['candidates']:
             block_reason = ai_data.get('promptFeedback', {}).get('blockReason', 'Necunoscut')
             print(f"🚫 Răspuns AI (similar) blocat sau gol. Motiv: {block_reason}")
             return jsonify({"error": f"Răspunsul AI a fost blocat sau este gol. Motiv: {block_reason}"}), 500

        ai_text_response = ai_data['candidates'][0]['content']['parts'][0]['text']
        if ai_text_response.strip().startswith('```json'):
            ai_text_response = ai_text_response.strip()[7:-3].strip()
        recomandari_json = json.loads(ai_text_response)
        return jsonify(recomandari_json), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Eroare de rețea la apelarea API-ului AI: {e}"}), 500
    except (KeyError, IndexError):
         print(f"❌ Răspuns invalid (similar) de la AI: {ai_data}")
         return jsonify({"error": "Răspuns invalid de la API-ul AI (Structură neașteptată)"}), 500
    except json.JSONDecodeError:
         print(f"❌ AI (similar) nu a returnat JSON valid:\n{ai_text_response}")
         return jsonify({"error": "AI-ul nu a returnat un JSON valid", "raspuns_ai": ai_text_response}), 500

@app.route("/api/recomandari/chestionar", methods=['POST'])
@jwt_required()
def recommend_from_questionnaire():
    GEMINI_API_KEY = 'AIzaSyBLXlCEedQBK1I62TxDiuCNnN5T_glyuiE' # Cheia ta
    GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent?key={GEMINI_API_KEY}"

    data = request.get_json()
    genuri = data.get('genuri', [])
    teme = data.get('teme', '')
    carte_exemplu = data.get('carte_exemplu', '')
    limba = data.get('limba', 'ro')
    if not genuri and not teme and not carte_exemplu:
        return jsonify({"error": "Te rugăm să specifici cel puțin un gen, o temă sau o carte exemplu."}), 400

    # Setări limbă
    lingua_dict = {
        'ro': {
            'greeting': 'Ești un expert în literatură. Vreau să îmi recomanzi 5 cărți bazate pe următoarele preferințe:',
            'language_note': 'IMPORTANT: Recomandă NUMAI cărți în limba ROMÂNĂ. Titlurile și autorii trebuie să fie în limba română.',
            'genres': 'Îmi plac genurile:',
            'themes': 'Mă interesează teme precum:',
            'example_book': 'O carte care mi-a plăcut recent este:',
            'instruction': 'Generează recomandări care combină aceste elemente.',
            'format': 'Răspunde doar cu un format JSON valid, ca o listă de obiecte cu cheile "titlu", "autor", "motivare".',
            'no_extra': 'Nu adăuga text extra.'
        },
        'en': {
            'greeting': 'You are a literature expert. I want you to recommend 5 books based on the following preferences:',
            'language_note': 'IMPORTANT: Recommend ONLY books originally written in ENGLISH or well-known English translations. Book titles and author names must be in English.',
            'genres': 'I like these genres:',
            'themes': 'I am interested in themes such as:',
            'example_book': 'A book I enjoyed recently is:',
            'instruction': 'Generate recommendations that combine these elements.',
            'format': 'Reply only with valid JSON format, as a list of objects with the keys "titlu", "autor", "motivare".',
            'no_extra': 'Do not add extra text.'
        }
    }

    lang_config = lingua_dict.get(limba, lingua_dict['ro'])

    prompt_parts = [lang_config['greeting']]
    prompt_parts.append(lang_config['language_note'])
    if genuri: prompt_parts.append(f"- {lang_config['genres']} {', '.join(genuri)}.")
    if teme: prompt_parts.append(f"- {lang_config['themes']} {teme}.")
    if carte_exemplu: prompt_parts.append(f"- {lang_config['example_book']} '{carte_exemplu}'.")
    prompt_parts.append(lang_config['instruction'])
    prompt_parts.append(lang_config['format'])
    prompt_parts.append(lang_config['no_extra'])
    prompt_text = "\n".join(prompt_parts)
    print(f"📄 Prompt trimis la AI (Chestionar - Limba: {limba}):\n{prompt_text}")
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}

    try:
        response = requests.post(GEMINI_API_URL, json=payload, headers={'Content-Type': 'application/json'})
        if response.status_code != 200:
            error_details = response.json() if response.headers.get('content-type') == 'application/json' else {"text": response.text}
            print(f"❌ Eroare de la API-ul AI (Chestionar): {response.status_code} - {error_details}")
            return jsonify({
                "error": f"API-ul Google AI a eșuat cu status {response.status_code}",
                "detalii": error_details, "url_apelat": GEMINI_API_URL
            }), 500

        ai_data = response.json()
        if 'candidates' not in ai_data or not ai_data['candidates']:
             block_reason = ai_data.get('promptFeedback', {}).get('blockReason', 'Necunoscut')
             print(f"🚫 Răspuns AI (Chestionar) blocat sau gol. Motiv: {block_reason}")
             return jsonify({"error": f"Răspunsul AI a fost blocat sau este gol. Motiv: {block_reason}"}), 500

        ai_text_response = ai_data['candidates'][0]['content']['parts'][0]['text']
        print(f"📄 Răspuns raw de la AI:\n{ai_text_response}")
        
        # Curăță JSON dacă e cu markdown code block
        if ai_text_response.strip().startswith('```json'):
            ai_text_response = ai_text_response.strip()[7:-3].strip()
        elif ai_text_response.strip().startswith('```'):
            ai_text_response = ai_text_response.strip()[3:-3].strip()
        
        # Încercă să parseze JSON
        try:
            recomandari_json = json.loads(ai_text_response)
        except json.JSONDecodeError as je:
            print(f"❌ JSON Decode Error (Chestionar): {je}")
            print(f"📄 Text care nu a putut fi parsurat:\n{ai_text_response[:500]}")
            # Încearcă cu fallback - poate e array în array
            if isinstance(ai_text_response, str):
                # Caută array-ul JSON în răspuns
                import re
                json_match = re.search(r'\[[\s\S]*\]', ai_text_response)
                if json_match:
                    recomandari_json = json.loads(json_match.group())
                else:
                    raise ValueError("Nu s-a găsit JSON valid în răspuns")
        
        return jsonify(recomandari_json), 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Eroare de rețea (Chestionar): {e}")
        return jsonify({"error": f"Eroare de rețea la apelarea API-ului AI: {e}"}), 500
    except (KeyError, IndexError) as e:
        print(f"❌ Răspuns invalid (Chestionar) de la AI: {e}")
        try:
            print(f"AI Data: {ai_data}")
        except:
            pass
        return jsonify({"error": "Răspuns invalid de la API-ul AI (Structură neașteptată)"}), 500
    except json.JSONDecodeError as e:
        print(f"❌ AI (Chestionar) nu a returnat JSON valid: {e}")
        try:
            print(f"Răspuns: {ai_text_response[:500]}")
        except:
            pass
        return jsonify({"error": "AI-ul nu a returnat un JSON valid"}), 500
    except Exception as e:
        print(f"❌ Eroare generală (Chestionar): {e}")
        return jsonify({"error": f"Eroare neașteptată: {str(e)}"}), 500

# --- RUTĂ NOUĂ PENTRU A GĂSI URMĂTOAREA CARTE DIN SERIE ---
@app.route("/api/recomandari/serie", methods=['POST'])
@jwt_required()
def find_next_in_series():
    GEMINI_API_KEY = 'AIzaSyBLXlCEedQBK1I62TxDiuCNnN5T_glyuiE' # Cheia AI
    API_KEY_BOOKS = 'AIzaSyBLXlCEedQBK1I62TxDiuCNnN5T_glyuiE' # Aceeași cheie
    GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent?key={GEMINI_API_KEY}"

    data = request.get_json()
    id_raft_curent = data.get('id_raft')
    if not id_raft_curent:
         return jsonify({"error": "Lipseste ID-ul cărții de pe raft"}), 400

    try:
        # Găsim cartea în baza noastră de date folosind id_raft
        carte_curenta = db.session.query(Raft, Carti).join(
            Carti, Raft.id_carte == Carti.id
        ).filter(
            Raft.id == id_raft_curent
        ).first()

        if not carte_curenta:
            return jsonify({"error": "Cartea nu a fost găsită pe raft"}), 404
        
        raft_entry, carte_info = carte_curenta
        id_google_carte = carte_info.id_google
        print(f"🔍 Caut seria pentru cartea: {carte_info.titlu} (id_google: {id_google_carte})")
        
        serie_nume = carte_info.serie_nume
        serie_volum_str = carte_info.serie_volum
        toate_cartile_serie = []

        # --- EXTRAGERE SERIA DIN GOOGLE BOOKS (dacă nu o avem în DB) ---
        if not serie_nume or not serie_volum_str:
            print(f"⚠️ Seria nu e în DB. Extragi din Google Books...")
            try:
                detalii_url = f"https://www.googleapis.com/books/v1/volumes/{id_google_carte}?key={API_KEY_BOOKS}"
                detalii_response = requests.get(detalii_url)
                if detalii_response.status_code == 200:
                    detalii_data = detalii_response.json()
                    volume_info = detalii_data.get('volumeInfo', {})
                    series_info = volume_info.get('seriesInfo', {}).get('bookSeries', [])
                    if series_info:
                        first_series = series_info[0]
                        serie_nume = first_series.get('seriesId', None)
                        serie_volum_str = str(first_series.get('memberNumber') or first_series.get('orderNumber') or '1')
                        print(f"✅ Seria extrasă din Google: {serie_nume} Vol: {serie_volum_str}")
                    else:
                        print(f"⚠️ Google Books nu are info de serie. Voi folosi titlul cărții pentru deducție...")
                        # ALTERNATIVĂ: Folosim titlul cărții ca bază pentru căutare
                        titlu = volume_info.get('title', '')
                        print(f"📖 Titlu carte: {titlu}")
                        
                        # Încercam să deducem seria din titlu (ex: "Harry Potter and the..." => "Harry Potter")
                        # Luăm primele cuvinte pana la anumite pattern-uri
                        import re
                        
                        # Pattern: "Name - Vol X" sau "Name: Book X" 
                        pattern_match = re.match(r'([^-:0-9]+)', titlu)
                        if pattern_match:
                            serie_dedusa = pattern_match.group(1).strip()
                            # Scoatem cuvintele foarte scurte
                            if len(serie_dedusa) > 3:
                                serie_nume = serie_dedusa
                                print(f"📝 Serie dedusă din titlu: {serie_nume}")
                        
                        # Căutam volume în titlu
                        volum_match = re.search(r'[Vv]ol[ume]*\.?\s*(\d+)|[Bb]ook\s*(\d+)|#\s*(\d+)', titlu)
                        if volum_match:
                            for group in volum_match.groups():
                                if group:
                                    serie_volum_str = str(group)
                                    print(f"🔢 Volum dedus din titlu: {serie_volum_str}")
                                    break
            except Exception as e_extract:
                print(f"⚠️ Eroare la extragerea seriei din Google: {e_extract}")
                import traceback
                traceback.print_exc()

        # --- METODA 1: Căutare Google Books - TOATE CĂRȚILE DIN SERIE ---
        if serie_nume:
            try:
                print(f"🔍 Caut Google Books: TOATĂ seria '{serie_nume}'")
                # Căutăm seria - maxResults 20 pentru a obține mai multe volume
                # Varianta 1: Cu ghilimele
                search_query = f"\"{serie_nume}\""
                search_url = f"https://www.googleapis.com/books/v1/volumes?q={search_query}&key={API_KEY_BOOKS}&maxResults=40"
                
                print(f"📡 URL apelat: {search_url}")
                search_response = requests.get(search_url)
                print(f"📊 Status Google Books: {search_response.status_code}")
                
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    print(f"📚 Cărți găsite: {len(search_data.get('items', []))}")
                    
                    if 'items' in search_data:
                        # Extragem toate cărțile și le organizăm după volum
                        carti_temp = []
                        for idx, item in enumerate(search_data['items']):
                            info = item.get('volumeInfo', {})
                            titlu = info.get('title', 'N/A')
                            autori = info.get('authors', ['N/A'])
                            
                            # Încercăm să extragem seria și volumul
                            series_info = info.get('seriesInfo', {}).get('bookSeries', [])
                            volum_nr = None
                            gasit_in_seria = False
                            
                            print(f"  [{idx}] {titlu} - Series info: {series_info}")
                            
                            if series_info:
                                for ser in series_info:
                                    ser_name = ser.get('seriesId', '')
                                    print(f"      Verific seria: '{ser_name}' vs '{serie_nume}'")
                                    
                                    # Potrivire flexibilă
                                    if (serie_nume.lower() in ser_name.lower() or 
                                        ser_name.lower() in serie_nume.lower() or
                                        ser_name.lower() == serie_nume.lower()):
                                        
                                        gasit_in_seria = True
                                        # Încercăm să extragem volumul
                                        try:
                                            volum_raw = ser.get('memberNumber') or ser.get('orderNumber')
                                            if volum_raw:
                                                volum_nr = float(volum_raw)
                                                print(f"      ✅ Volum găsit: {volum_nr}")
                                            else:
                                                volum_nr = 0
                                        except Exception as e_vol:
                                            print(f"      ⚠️ Eroare la volum: {e_vol}")
                                            volum_nr = 0
                                        break
                            
                            if gasit_in_seria or volum_nr is not None:
                                carte_obj = {
                                    "titlu": titlu,
                                    "autor": ', '.join(autori),
                                    "volum": volum_nr if volum_nr is not None else 999,  # 999 pentru cărți fără volum clar
                                    "id_google": item.get('id', 'N/A')
                                }
                                carti_temp.append(carte_obj)
                                print(f"      ➕ Adăugată în rezultate: volum={carte_obj['volum']}")
                        
                        print(f"📝 Total cărți în rezultate temp: {len(carti_temp)}")
                        
                        if carti_temp:
                            # Sortăm după volum
                            carti_temp.sort(key=lambda x: x['volum'] if isinstance(x['volum'], (int, float)) else 999)
                            
                            # Formatăm rezultatul cu numerotare
                            for idx, carte in enumerate(carti_temp, 1):
                                volum_display = int(carte['volum']) if carte['volum'] and carte['volum'] < 100 else idx
                                toate_cartile_serie.append({
                                    "volum": volum_display,
                                    "titlu": carte['titlu'],
                                    "autor": carte['autor'],
                                    "id_google": carte['id_google']
                                })
                            
                            print(f"✅ Google Books a găsit {len(toate_cartile_serie)} cărți din seria '{serie_nume}'")
                else:
                    print(f"❌ Google Books status: {search_response.status_code}")
                            
            except Exception as e_gb:
                 print(f"⚠️ Eroare la căutarea Google Books: {e_gb}")
                 import traceback
                 traceback.print_exc()

        # --- METODA 1B: Dacă Metoda 1 a eșuat, căutare mai simplă (doar titlu) ---
        if not toate_cartile_serie and serie_nume:
            try:
                print(f"🔄 Metoda 1 a eșuat. Încerca căutare simplă după titlu...")
                # Căutare mai simplă - doar cuvintele din titlul seriei
                search_query = serie_nume
                search_url = f"https://www.googleapis.com/books/v1/volumes?q={search_query}&key={API_KEY_BOOKS}&maxResults=40"
                
                print(f"📡 URL apelat (căutare simplă): {search_url}")
                search_response = requests.get(search_url)
                
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    print(f"📚 Rezultate găsite: {len(search_data.get('items', []))}")
                    
                    if 'items' in search_data and search_data['items']:
                        # Luăm primele 10 rezultate care par relevante
                        for item in search_data['items'][:20]:
                            info = item.get('volumeInfo', {})
                            titlu = info.get('title', '')
                            
                            # Filtru simplu: titlul trebuie să conțină cuvintele cheie din serie
                            if any(cuvant.lower() in titlu.lower() for cuvant in serie_nume.split()):
                                autori = info.get('authors', ['N/A'])
                                
                                # Încerc să extrag volumul din titlu (ex: "Serie Name - Vol 1")
                                volum_nr = None
                                try:
                                    # Căutăm numere în titlu
                                    import re
                                    numere = re.findall(r'\d+', titlu)
                                    if numere:
                                        volum_nr = int(numere[0])
                                except:
                                    pass
                                
                                toate_cartile_serie.append({
                                    "volum": volum_nr if volum_nr else len(toate_cartile_serie) + 1,
                                    "titlu": titlu,
                                    "autor": ', '.join(autori),
                                    "id_google": item.get('id', 'N/A')
                                })
                        
                        # Sortăm după volum
                        toate_cartile_serie.sort(key=lambda x: x['volum'])
                        
                        if toate_cartile_serie:
                            print(f"✅ Căutare simplă a găsit {len(toate_cartile_serie)} cărți")
            except Exception as e_simple:
                print(f"⚠️ Eroare la căutarea simplă: {e_simple}")
                import traceback
                traceback.print_exc()

        # --- METODA 2: AI Fallback - dacă Google nu a găsit seria ---
        if not toate_cartile_serie and serie_nume:
            print("🤔 Google Books nu a găsit seria. Întreb AI-ul pentru lista completa...")
            prompt_text = f"Ești un expert în serii de cărți. Care sunt TOATE cărțile din seria '{serie_nume}'? Enumează-le în ordine, cu volumul și autorul. Răspunde DOAR cu un JSON valid - un array de obiecte cu cheile: 'volum' (număr), 'titlu' (string), 'autor' (string). Nu adăuga text suplimentar. Exemplu: [{{'volum': 1, 'titlu': 'Book 1', 'autor': 'Author'}}, {{'volum': 2, 'titlu': 'Book 2', 'autor': 'Author'}}]"
            payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
            
            try:
                response = requests.post(GEMINI_API_URL, json=payload, headers={'Content-Type': 'application/json'})
                if response.status_code != 200:
                     raise requests.exceptions.RequestException(f"API-ul AI a eșuat cu status {response.status_code}")

                ai_data = response.json()
                if 'candidates' not in ai_data or not ai_data['candidates']:
                    raise ValueError("Răspuns AI blocat sau gol")
                    
                ai_text_response = ai_data['candidates'][0]['content']['parts'][0]['text']
                
                # Curățăm răspunsul AI
                if '```json' in ai_text_response:
                    ai_text_response = ai_text_response.split('```json')[1].split('```')[0].strip()
                elif '```' in ai_text_response:
                    ai_text_response = ai_text_response.split('```')[1].split('```')[0].strip()
                
                toate_cartile_serie = json.loads(ai_text_response)
                print(f"✅ AI a găsit {len(toate_cartile_serie)} cărți din seria '{serie_nume}'")
            except Exception as e_ai:
                 print(f"❌ Eroare la apelarea AI: {e_ai}")
                 import traceback
                 traceback.print_exc()

        # --- Returnăm toate cărțile din serie ---
        if toate_cartile_serie:
            return jsonify({
                "seria_nume": serie_nume,
                "carti": toate_cartile_serie
            }), 200
        elif not serie_nume:
            # Nu am putut deduce seria
            return jsonify({
                "error": f"Nu am putut identifica seria pentru cartea '{carte_info.titlu}'. Cartea nu pare să facă parte dintr-o serie cunoscută."
            }), 404
        else:
            # Am seria dar nu am găsit cărțile
            return jsonify({
                "error": f"Nu am putut găsi cărți din seria '{serie_nume}'. Google Books nu are informații complete despre această serie."
            }), 404

    except Exception as e:
        print(f"❌ Eroare majoră în find_next_in_series: {str(e)}")
        return jsonify({"error": str(e)}), 500


# --- RUTĂ NOUĂ PENTRU RECOMANDĂRI PE STARE (MOOD) ---
@app.route("/api/recomandari/mood", methods=['POST'])
def get_mood_recommendations():
    """
    Recomandă cărți bazate pe starea emoțională a utilizatorului
    Body: { "stare": "amuzant", "limba": "ro" (optional) }
    """
    GEMINI_API_KEY = 'AIzaSyBLXlCEedQBK1I62TxDiuCNnN5T_glyuiE'
    GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent?key={GEMINI_API_KEY}"

    data = request.get_json()
    stare = data.get('stare', '').lower().strip()
    stare_custom = data.get('stare_custom', '').strip()
    limba = data.get('limba', 'ro')
    
    # Verificare: trebuie să aibă fie o stare predefinită, fie o stare custom
    if not stare and not stare_custom:
        return jsonify({"error": "Trebuie să selectezi o stare sau să scrii o stare personalizată"}), 400

    # Mapping-ul stărilor la descrieri
    mood_descriptions = {
        'amuzant': 'amuzant și relaxant, cu umor și personaje simpatice. Evită dramele grele.',
        'thriller': 'thriller care ține treaz, plin de suspans și roade. Trebuie să fie captivant.',
        'dragoste': 'o poveste de dragoste tristă și emoționantă, cu sentiment și melancolie.',
        'aventura': 'o aventură épică și palpitantă, plină de acțiune și descoperiri.',
        'mistery': 'un mister captivant cu scene de crimă și investigații, plin de tensiune.',
        'fantasia': 'fantasia cu lumi imaginare și magie, potrivit pentru evadare din realitate.',
        'personal': 'un roman de dezvoltare personală care inspiră și motivează.',
    }

    # Gasim descrierea stării - prioritate pentru custom
    if stare_custom:
        stare_desc = stare_custom
        stare_label = "Custom"
    else:
        stare_desc = mood_descriptions.get(stare, stare)
        stare_label = stare

    print(f"🎭 Recomandări Mood: '{stare_label}' ({stare_desc}) - Limba: {limba}")

    # Setări limbă
    lingua_dict = {
        'ro': {
            'lang': 'română',
            'instruction': 'Ești un recomandator expert de cărți. Recomandă EXACT 3 cărți care se potrivesc acestei stări emoționale:',
            'language_note': 'IMPORTANT: Recomandă NUMAI cărți în limba ROMÂNĂ. Titlurile și autorii trebuie să fie în limba română.',
            'example': 'EXEMPLU FORMAT:',
            'answer': 'Răspunde DOAR cu un JSON valid - un array de obiecte cu EXACT aceste chei:',
            'title': 'titlu (string)',
            'author': 'autor (string)',
            'reason': 'motivare (string - explicație de 1-2 rânduri de ce se potrivește)',
            'only_json': 'Nu adauga text suplimentar, DOAR JSON-ul.'
        },
        'en': {
            'lang': 'English',
            'instruction': 'You are an expert book recommender. Recommend EXACTLY 3 books that match this emotional state:',
            'language_note': 'IMPORTANT: Recommend ONLY books originally written in ENGLISH or well-known English translations. Book titles and author names must be in English.',
            'example': 'EXAMPLE FORMAT:',
            'answer': 'Reply ONLY with valid JSON - an array of objects with EXACTLY these keys:',
            'title': 'title (string)',
            'author': 'author (string)',
            'reason': 'reason (string - 1-2 lines explanation why it fits)',
            'only_json': 'Do not add extra text, ONLY the JSON.'
        }
    }

    lang_config = lingua_dict.get(limba, lingua_dict['ro'])

    prompt_text = f"""{lang_config['instruction']}

{lang_config['language_note']}

STARE: {stare_desc}

{lang_config['answer']}
- {lang_config['title']}
- {lang_config['author']}
- {lang_config['reason']}

{lang_config['example']}
[
  {{"titlu": "Cartea 1", "autor": "Autor 1", "motivare": "Explicație scurtă..."}},
  {{"titlu": "Cartea 2", "autor": "Autor 2", "motivare": "Explicație scurtă..."}},
  {{"titlu": "Cartea 3", "autor": "Autor 3", "motivare": "Explicație scurtă..."}}
]

{lang_config['only_json']}"""

    try:
        payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
        response = requests.post(GEMINI_API_URL, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code != 200:
            print(f"❌ Gemini API status: {response.status_code}")
            error_details = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            return jsonify({"error": f"API-ul AI a eșuat cu status {response.status_code}", "detalii": error_details}), 500

        ai_data = response.json()
        if 'candidates' not in ai_data or not ai_data['candidates']:
            block_reason = ai_data.get('promptFeedback', {}).get('blockReason', 'Necunoscut')
            print(f"❌ Răspuns AI (Mood) gol sau blocat. Motiv: {block_reason}")
            return jsonify({"error": f"Răspuns AI blocat sau gol. Motiv: {block_reason}"}), 500
        
        ai_text = ai_data['candidates'][0]['content']['parts'][0]['text']
        print(f"📝 Răspuns AI brut (Mood):\n{ai_text[:200]}...")

        # Curățăm răspunsul AI
        if '```json' in ai_text:
            ai_text = ai_text.split('```json')[1].split('```')[0].strip()
        elif '```' in ai_text:
            ai_text = ai_text.split('```')[1].split('```')[0].strip()

        recomandari_list = json.loads(ai_text)
        
        # Validare că sunt cărți
        if not isinstance(recomandari_list, list) or len(recomandari_list) < 1:
            print(f"❌ Răspuns AI invalid - nu e o listă sau e goală")
            return jsonify({"error": "Răspuns AI invalid - nu e o listă de cărți"}), 500

        print(f"✅ AI a recomandat {len(recomandari_list)} cărți pentru starea '{stare}'")
        
        return jsonify(recomandari_list), 200

    except json.JSONDecodeError as e:
        print(f"❌ Eroare JSON parse (Mood): {e}")
        try:
            print(f"Răspuns AI: {ai_text[:300]}")
        except:
            pass
        return jsonify({"error": f"Răspuns AI invalid - JSON parse failed"}), 500
    except Exception as e:
        print(f"❌ Eroare în get_mood_recommendations: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Eroare: {str(e)}"}), 500


# --- RUTĂ PENTRU GENERARE REZUMATE AI ---
@app.route("/api/recomandari/rezumat", methods=['POST'])
def generate_book_summary():
    """
    Generează un rezumat AI pentru o carte
    Body: { "titlu": "Dune", "autor": "Frank Herbert", "descriere": "..." (optional), "limba": "ro" (optional) }
    Returns: { "rezumat": "Rezumat de ~100 cuvinte...", "titlu": "Dune" }
    """
    data = request.get_json()
    titlu = data.get('titlu', '').strip()
    autor = data.get('autor', '').strip()
    descriere = data.get('descriere', '').strip()
    limba = data.get('limba', 'ro').lower()
    
    if not titlu or not autor:
        return jsonify({"error": "Titlu și autor sunt obligatorii"}), 400
    
    print(f"📖 Se generează rezumat pentru: {titlu} de {autor} - Limba: {limba}")
    
    try:
        # Setări limbă
        lingua_dict = {
            'ro': {
                'intro': 'Tu ești critic literar. Generează un rezumat concis de EXACT 100 de cuvinte pentru cartea:',
                'with_desc': 'Descriere din Google Books:',
                'caption': 'Rezumatul trebuie să fie captivant, concis și să prezinte esența cărții.',
                'instruction': 'Răspunde DOAR cu textul rezumatului, fără explicații suplimentare.'
            },
            'en': {
                'intro': 'You are a literary critic. Generate a concise summary of EXACTLY 100 words for the book:',
                'with_desc': 'Description from Google Books:',
                'caption': 'The summary must be captivating, concise and present the essence of the book.',
                'instruction': 'Reply ONLY with the summary text, without additional explanations.'
            }
        }

        lang_config = lingua_dict.get(limba, lingua_dict['ro'])

        # Construim prompt pentru AI
        if descriere:
            prompt_text = f"""{lang_config['intro']}

Titlu: {titlu}
Autor: {autor}
{lang_config['with_desc']} {descriere}

{lang_config['caption']} {lang_config['instruction']}"""
        else:
            prompt_text = f"""{lang_config['intro']}

Titlu: {titlu}
Autor: {autor}

{lang_config['caption']} {lang_config['instruction']}"""
        
        print(f"📄 Prompt AI ({limba}):\n{prompt_text}")
        
        GEMINI_API_KEY = 'AIzaSyBLXlCEedQBK1I62TxDiuCNnN5T_glyuiE'
        GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent?key={GEMINI_API_KEY}"
        
        payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
        response = requests.post(GEMINI_API_URL, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code != 200:
            print(f"❌ Gemini API status: {response.status_code}")
            return jsonify({"error": f"API-ul AI a eșuat cu status {response.status_code}"}), 500

        ai_data = response.json()
        if 'candidates' not in ai_data or not ai_data['candidates']:
            print(f"❌ Răspuns AI gol sau blocat")
            return jsonify({"error": "Răspuns AI blocat sau gol"}), 500
        
        rezumat = ai_data['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # Curățim textul
        if rezumat.startswith('```'):
            rezumat = rezumat.split('\n', 1)[1]
        if rezumat.endswith('```'):
            rezumat = rezumat.rsplit('\n', 1)[0]
        rezumat = rezumat.strip()
        
        print(f"✅ Rezumat generat cu succes ({len(rezumat.split())} cuvinte)")
        
        return jsonify({
            "rezumat": rezumat,
            "titlu": titlu,
            "autor": autor
        }), 200

    except Exception as e:
        print(f"❌ Eroare în generate_book_summary: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Eroare: {str(e)}"}), 500



# -----------------------------------------------------------------
# ERROR HANDLERS PENTRU JWT
# -----------------------------------------------------------------
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print("⚠️ Token JWT expirat!")
    return jsonify({"error": "Token JWT expirat"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"❌ Token JWT invalid: {error}")
    return jsonify({"error": f"Token JWT invalid: {error}"}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    print(f"❌ Token JWT lipsă: {error}")
    return jsonify({"error": f"Token JWT lipsă: {error}"}), 401

# 4. PORNIRE SERVER
if __name__ == '__main__':
    app.run(port=5000, debug=True)
