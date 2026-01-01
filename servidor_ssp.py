from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Lista para armazenar os alertas recebidos (em um app real seria um Banco de Dados)
historico_alertas = []

@app.route('/alerta', methods=['POST'])
def receber_alerta():
    dados = request.json
    dados['horario'] = datetime.now().strftime("%H:%M:%S")
    
    print("\n" + "="*40)
    print(f"!!! NOVO ALERTA RECEBIDO !!!")
    print(f"Vítima: {dados.get('usuario')}")
    print(f"Local: {dados.get('localizacao')}")
    print(f"Mensagem: {dados.get('mensagem')}")
    print("="*40 + "\n")
    
    historico_alertas.append(dados)
    return jsonify({"status": "sucesso", "mensagem": "Alerta registrado na Central"}), 200

if __name__ == '__main__':
    # Roda o servidor na sua rede local
    app.run(host='0.0.0.0', port=5000)