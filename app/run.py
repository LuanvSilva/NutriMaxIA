import sys
import os

# Adicionar o diretório atual ao path do Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importação local sem o prefixo "app"
from __init__ import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True) # debug=True apenas para desenvolvimento