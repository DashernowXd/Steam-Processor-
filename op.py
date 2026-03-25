import os
import string
import re 
import nltk
import pandas as pd
import numpy as np
from scipy.interpolate import make_interp_spline
import matplotlib.pyplot as plt
import pydocx as pdx


##importacion de librerias 
from PyPDF2 import PdfReader
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.probability import FreqDist
from scipy.optimize import curve_fit
##complementos de nltk
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')
##informacion del corpus
stopWords=set(stopwords.words('spanish'))
route="C:/Users/abelp/OneDrive/Escritorio/Information_Recovery/Information_Recovery/p2/interfaz/interfaz/static/corpus/1984.pdf"

from flask import Flask, render_template, request
