##importacion de librerias
import os
import string
import re 
import nltk
import pandas as pd
import numpy as np
from scipy.interpolate import make_interp_spline
import matplotlib.pyplot as plt

##importacion de librerias 
from PyPDF2 import PdfReader
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import SnowballStemmer
from docx import Document as pdox
from openpyxl import workbook
from nltk.probability import FreqDist
from collections import defaultdict

##complementos de nltk
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')
##informacion del corpus
stopWords=set(stopwords.words('spanish'))
route="C:/Users/abelp/OneDrive/Escritorio/Information_Recovery/Information_Recovery/p2/interfaz/interfaz/static/corpus/1984.pdf"

routePreprocessing="C:/Users/abelp/OneDrive/Escritorio/Information_Recovery/Information_Recovery/p2/interfaz/interfaz/static/preprocesadoSteps/"
##importacion de librerias de flask
from flask import Flask, render_template, request
#inicio de la aplicacion
app = Flask(__name__)

##ruta de la carpeta corpus
CORPUS_DIR = os.path.join(os.getcwd(), "C:\\Users\\abelp\\OneDrive\\Escritorio\\interfaz\\static\\corpus")
def zipf_law(x, a, b):
    return a / x**b

##Ruta principal de la aplicacion
@app.route("/", methods=["GET", "POST"])
def index():
    ##Lectura de archivos en la carpeta corpus
    if not os.path.exists(CORPUS_DIR):
        return "La carpeta 'corpus' no existe. Por favor, créala y agrega archivos."

    files = os.listdir(CORPUS_DIR)
    #file_paths = [os.path.join(CORPUS_DIR, file) for file in files]
    file_paths = [f"static/corpus/{file}" for file in files]
    #print(files)
##barra de busqueda
    if request.method == "POST":
        query = request.form.get("search")  
        print(f"Buscaste: {query}")  
        
        print(file_paths)
        return render_template("index.html", file_paths=file_paths, query=query)

    
    return render_template("index.html", file_paths=file_paths)
##selector de archivos
@app.route("/select_archive", methods=["POST"])
def select_archive():
    filename = request.form.get('path')
##ruta del archivo seleccionado
    if filename:
        
        if filename.endswith(".pdf"):
               text=""
               reader=PdfReader(filename)
               for i in range(3):
                text+=reader.pages[i].extract_text()
                return f"El archivo seleccionado es un pdf {text}"
        if filename.endswith(".txt"):
            file=open(filename, 'r', encoding='utf-8', errors='ignore')
            text = file.read()
            return f"El archivo seleccionado es un txt {text}"
        
        if filename.endswith(".docx"):

            return f"El archivo seleccionado es un docx"
        
        
    return "No se seleccionó ningún archivo"

##ruta para mostrar los tokens

def leer_docx(ruta_archivo):
    doc = pdox(ruta_archivo)
    # Extrae el texto de todos los párrafos y lo convierte en un solo string
    return "\n".join([p.text for p in doc.paragraphs])


@app.route("/Preproccesor", methods=['GET', 'POST'])
def preprocesingDir():
    docs = os.listdir(CORPUS_DIR)
    #file_paths = [os.path.join(CORPUS_DIR, file) for file in files]
    #file_paths = [f"static/corpus/{file}" for file in files]
    textDocx=""
    textPdf=""
    text=""
    words_pdf=[]
    words_docx=[]
    words_txt=[]
    wordsTextCaps=[]
    wordsDocxCaps=[]
    wordsPDFCaps=[]


    for f in docs:
        file_path = os.path.join(CORPUS_DIR, f)
        
        if f.endswith(".pdf"):
            reader=PdfReader(route)
            for i in range(3):
                textPdf=reader.pages[i].extract_text()
            words_pdf.extend(word_tokenize(textPdf.lower()))
            wordsPDFCaps.extend(word_tokenize(textPdf))
                
            

        if f.endswith(".docx"):
            textDocx=leer_docx(file_path)+"\n"
            words_docx.extend(word_tokenize(textDocx.lower()))    
            wordsDocxCaps.extend(word_tokenize(textDocx))


        if f.endswith(".txt"):
            file=open(file_path, 'r', encoding='utf-8', errors='ignore')
            text = file.read()
            words_txt.extend(word_tokenize(text.lower()))
            wordsTextCaps.extend(word_tokenize(text))





        wordsPdfLower=[word for word in words_pdf if word.isalpha() ]
        wordsTxtLower=[word for word  in words_txt if word.isalpha() ] 
        wordsDocxLower=[word for word in words_docx if word.isalpha()]

        wordsDocx=[word for word in wordsDocxCaps if word.isalpha()]
        wordsPDF=[word for word in wordsPDFCaps if word.isalpha()]
        wordsText=[word for word in wordsTextCaps if word.isalpha()]

        wordsFiltreDocx=[word for word in wordsDocxCaps if word.isalpha() and word not in stopWords]
        wordsFiltrePDF=[word for word in wordsPDFCaps if word.isalpha() and word not in stopWords]
        wordsFiltreText=[word for word in wordsTextCaps if word.isalpha() and word not in stopWords]

        allLower=(
            wordsDocxLower + wordsPdfLower + wordsTxtLower
        )
        AllWords=(
            wordsText + wordsPDF + wordsDocx
        )
        AllfiltredWords=(
            wordsFiltreDocx + wordsFiltrePDF + wordsFiltreText
        )
        AllfiltredWords = list(set(AllfiltredWords))

        frequenceAllLower=FreqDist(allLower)
        frequendeWords=FreqDist(AllWords)
        frequenceAllFiltredWords=FreqDist(AllfiltredWords)

        df_Dicctionary3=pd.DataFrame(frequenceAllFiltredWords.items(), columns=["Termino", "frecuencia"])
        df_Dicctionary2=pd.DataFrame(frequenceAllLower.items(), columns=["Termino" , "frecuencia"])
        df_Dicctionary1=pd.DataFrame(frequendeWords.items(), columns=["Termino", "Frequencia"])

        name1="1Diccionario.xlsx"
        name2="2DiccMinus.xlsx"
        name3="3DiccSinStopsWords.xlsx"
        name4="4DiccSteams.xlsx"

        stemmer=SnowballStemmer("spanish")
        stems=[stemmer.stem(word) for word in AllfiltredWords]

        df_Dicctionary4=pd.DataFrame(frequenceAllFiltredWords.items(), columns=["Terminos","frecuencia"])
        df_Dicctionary4["stems"]=stems


        Route1=os.path.join(routePreprocessing, name1)
        Route2=os.path.join(routePreprocessing, name2)
        Route3=os.path.join(routePreprocessing, name3)
        Route4=os.path.join(routePreprocessing, name4)


        #creacion de excels
        df_Dicctionary1.to_excel(Route1)
        df_Dicctionary2.to_excel(Route2)
        df_Dicctionary3.to_excel(Route3)
        df_Dicctionary4.to_excel(Route4)

    files = os.listdir(routePreprocessing)
    #file_paths = [os.path.join(CORPUS_DIR, file) for file in files]
    file_paths = [f"static/preprocesadoSteps/{file}" for file in files]
    #print(files)
        


        
    


    return render_template("preprocessing.html", file_paths=file_paths )

    





    
if __name__ == "__main__":
    app.run(debug=True)

