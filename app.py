# ==============================
# IMPORTS
# ==============================
import os
import nltk
import pandas as pd
from pathlib import Path
from PyPDF2 import PdfReader
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
from docx import Document as pdox
from nltk.probability import FreqDist
from flask import Flask, render_template, request

# ==============================
# CONFIGURACIÓN BASE
# ==============================
BASE_DIR = Path(__file__).resolve().parent

CORPUS_DIR = BASE_DIR / "static" / "corpus"
PREPROCESS_DIR = BASE_DIR / "static" / "preprocesadoSteps"

# Crear carpetas si no existen
CORPUS_DIR.mkdir(parents=True, exist_ok=True)
PREPROCESS_DIR.mkdir(parents=True, exist_ok=True)

# ==============================
# NLTK (seguro para producción)
# ==============================
NLTK_DATA_DIR = BASE_DIR / "nltk_data"
NLTK_DATA_DIR.mkdir(exist_ok=True)

nltk.data.path.append(str(NLTK_DATA_DIR))

try:
    stopWords = set(stopwords.words('spanish'))
except LookupError:
    nltk.download('stopwords', download_dir=str(NLTK_DATA_DIR))
    nltk.download('punkt', download_dir=str(NLTK_DATA_DIR))
    stopWords = set(stopwords.words('spanish'))

# ==============================
# FLASK APP
# ==============================
app = Flask(__name__)

# ==============================
# FUNCIONES AUXILIARES
# ==============================
def leer_docx(ruta_archivo):
    doc = pdox(ruta_archivo)
    return "\n".join([p.text for p in doc.paragraphs])

# ==============================
# RUTA PRINCIPAL
# ==============================
@app.route("/", methods=["GET", "POST"])
def index():
    files = os.listdir(CORPUS_DIR)
    file_paths = [f"static/corpus/{file}" for file in files]

    if request.method == "POST":
        query = request.form.get("search")
        return render_template("index.html", file_paths=file_paths, query=query)

    return render_template("index.html", file_paths=file_paths)

# ==============================
# SELECCIÓN DE ARCHIVO
# ==============================
@app.route("/select_archive", methods=["POST"])
def select_archive():
    filename = request.form.get('path')

    if filename:
        file_path = BASE_DIR / filename

        if filename.endswith(".pdf"):
            text = ""
            reader = PdfReader(str(file_path))
            for i in range(min(3, len(reader.pages))):
                text += reader.pages[i].extract_text() or ""
            return f"<pre>PDF:\n{text}</pre>"

        elif filename.endswith(".txt"):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
            return f"<pre>TXT:\n{text}</pre>"

        elif filename.endswith(".docx"):
            text = leer_docx(file_path)
            return f"<pre>DOCX:\n{text}</pre>"

    return "No se seleccionó ningún archivo"

# ==============================
# PREPROCESAMIENTO
# ==============================
@app.route("/Preproccesor", methods=['GET', 'POST'])
def preprocesingDir():

    docs = os.listdir(CORPUS_DIR)

    words_pdf, words_docx, words_txt = [], [], []
    wordsPDFCaps, wordsDocxCaps, wordsTextCaps = [], [], []

    for f in docs:
        file_path = CORPUS_DIR / f

        if f.endswith(".pdf"):
            reader = PdfReader(str(file_path))
            textPdf = ""
            for i in range(min(3, len(reader.pages))):
                textPdf += reader.pages[i].extract_text() or ""

            words_pdf.extend(word_tokenize(textPdf.lower()))
            wordsPDFCaps.extend(word_tokenize(textPdf))

        elif f.endswith(".docx"):
            textDocx = leer_docx(file_path)
            words_docx.extend(word_tokenize(textDocx.lower()))
            wordsDocxCaps.extend(word_tokenize(textDocx))

        elif f.endswith(".txt"):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
            words_txt.extend(word_tokenize(text.lower()))
            wordsTextCaps.extend(word_tokenize(text))

    # ==============================
    # LIMPIEZA
    # ==============================
    wordsPdfLower = [w for w in words_pdf if w.isalpha()]
    wordsTxtLower = [w for w in words_txt if w.isalpha()]
    wordsDocxLower = [w for w in words_docx if w.isalpha()]

    wordsPDF = [w for w in wordsPDFCaps if w.isalpha()]
    wordsText = [w for w in wordsTextCaps if w.isalpha()]
    wordsDocx = [w for w in wordsDocxCaps if w.isalpha()]

    wordsFiltreDocx = [w for w in wordsDocx if w not in stopWords]
    wordsFiltrePDF = [w for w in wordsPDF if w not in stopWords]
    wordsFiltreText = [w for w in wordsText if w not in stopWords]

    allLower = wordsDocxLower + wordsPdfLower + wordsTxtLower
    AllWords = wordsText + wordsPDF + wordsDocx
    AllFilteredWords = list(set(wordsFiltreDocx + wordsFiltrePDF + wordsFiltreText))

    # ==============================
    # FRECUENCIAS
    # ==============================
    freqLower = FreqDist(allLower)
    freqAll = FreqDist(AllWords)
    freqFiltered = FreqDist(AllFilteredWords)

    df1 = pd.DataFrame(freqAll.items(), columns=["Termino", "Frecuencia"])
    df2 = pd.DataFrame(freqLower.items(), columns=["Termino", "Frecuencia"])
    df3 = pd.DataFrame(freqFiltered.items(), columns=["Termino", "Frecuencia"])

    # ==============================
    # STEMMING
    # ==============================
    stemmer = SnowballStemmer("spanish")
    stems = [stemmer.stem(word) for word in AllFilteredWords]

    df4 = pd.DataFrame({
        "Termino": AllFilteredWords,
        "Stem": stems
    })

    # ==============================
    # GUARDAR EXCELS
    # ==============================
    df1.to_excel(PREPROCESS_DIR / "1Diccionario.xlsx", index=False)
    df2.to_excel(PREPROCESS_DIR / "2DiccMinus.xlsx", index=False)
    df3.to_excel(PREPROCESS_DIR / "3DiccSinStopWords.xlsx", index=False)
    df4.to_excel(PREPROCESS_DIR / "4DiccStems.xlsx", index=False)

    files = os.listdir(PREPROCESS_DIR)
    file_paths = [f"static/preprocesadoSteps/{file}" for file in files]

    return render_template("preprocessing.html", file_paths=file_paths)


# ==============================
# BUSCADOR CON STEMMING
# ==============================

@app.route("/search", methods=["POST"])
def search():

    query = request.form.get("search")

    if not query:
        return "No se ingresó búsqueda"

    stemmer = SnowballStemmer("spanish")

    query_lower = query.lower()
    query_stem = stemmer.stem(query_lower)

    results = []

    docs = os.listdir(CORPUS_DIR)

    for f in docs:
        file_path = CORPUS_DIR / f
        text = ""

        # ==============================
        # LECTURA
        # ==============================
        if f.endswith(".pdf"):
            reader = PdfReader(str(file_path))
            for i in range(min(3, len(reader.pages))):
                text += reader.pages[i].extract_text() or ""

        elif f.endswith(".docx"):
            text = leer_docx(file_path)

        elif f.endswith(".txt"):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
        else:
            continue

        # ==============================
        # PROCESAMIENTO
        # ==============================
        tokens = word_tokenize(text.lower())
        tokens = [w for w in tokens if w.isalpha()]

        stems = [stemmer.stem(w) for w in tokens]

        count_word = tokens.count(query_lower)
        count_stem = stems.count(query_stem)

        total = count_word + count_stem

        # 👉 SIEMPRE se agrega
        results.append({
            "archivo": f,
            "palabra": count_word,
            "stem": count_stem,
            "total": total
        })

    # ordenar por relevancia
    results = sorted(results, key=lambda x: x["total"], reverse=True)

    return render_template("resultados.html", query=query, results=results)


# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run(debug=True)