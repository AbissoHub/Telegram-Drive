import os
import sys

sys.path.insert(0, os.path.abspath('.'))

# Informazioni sul progetto
project = 'Telegram-Drive'
author = 'AbissoHub'
release = '0.1.0'

# Estensioni Sphinx utilizzate
extensions = [
    'sphinx.ext.autodoc', 
    'sphinx.ext.napoleon',  
    'sphinx.ext.viewcode',  
]

master_doc = 'index'

html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "")

# Segnalare a Jinja2 che il build è in esecuzione su Read the Docs
if os.environ.get("READTHEDOCS", "") == "True":
    if "html_context" not in globals():
        html_context = {}
    html_context["READTHEDOCS"] = True


