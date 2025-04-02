from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import yt_dlp
import whisper
import ffmpeg
import pandas as pd
from google.cloud import bigquery
from flask_cors import CORS

leagues = [
  {
    'name': 'UEFA Champions League',
    'id': 1,
    'teams': [
      {
        'name': 'Real Madrid',
        'id': '15',
        'stars': True,
        'goalsScored': 28,
        'goalsConceded': 17,
        'wins': 8,
        'draws': 0,
        'defeats': 4,
        'ballPossesion': 51.25,
        'passingEffectiveness': 90.34,
        'attacks': 612,
      },
      {
        'name': 'Arsenal',
        'id': '0',
        'stars': False,
        'goalsScored': 25,
        'goalsConceded': 6,
        'wins': 7,
        'draws': 2,
        'defeats': 1,
        'ballPossesion': 53.20,
        'passingEffectiveness': 86.90,
        'attacks': 514,
      },
      {
        'name': 'Barcelona',
        'id': '5',
        'stars': True,
        'goalsScored': 32,
        'goalsConceded': 14,
        'wins': 8,
        'draws': 1,
        'defeats': 1,
        'ballPossesion': 57.90,
        'passingEffectiveness': 88.00,
        'attacks': 494,
      },
    ],
  },
]

def encontrar_time(nome_time):
    """Busca o time pelo nome dentro da variável leagues."""
    for liga in leagues:
        for time in liga['teams']:
            if time['name'] == nome_time:
                return time
    return None

def calcular_probabilidades(partida):
    """Calcula a probabilidade de vitória, empate e derrota baseado nas estatísticas dos times."""

    # Encontrar os times na estrutura de dados
    time_casa = encontrar_time(partida['homeMach'])
    time_fora = encontrar_time(partida['visitingTeam'])

    # Se algum time não for encontrado, retornar erro
    if not time_casa or not time_fora:
        return {"erro": "Um dos times não foi encontrado."}

    def força(time):
        """Calcula a força do time com base em ataque, defesa, posse de bola, eficácia no passe e ataques."""
        jogos = time['wins'] + time['draws'] + time['defeats']
        
        # Calcular ataque e defesa baseados em gols
        ataque = time['goalsScored'] / jogos
        defesa = 1 / (time['goalsConceded'] + 1)  # Evitar divisão por zero

        # Calcular o impacto da posse de bola, eficácia no passe e número de ataques
        posse_bola = time['ballPossesion'] / 100  # Normalizando para um valor entre 0 e 1
        passes_eficazes = time['passingEffectiveness'] / 100  # Normalizando para um valor entre 0 e 1
        ataques = time['attacks'] / jogos  # Normalizando o número de ataques

        # Combinar todas as variáveis para calcular a força total
        força_total = (ataque * 0.3) + (defesa * 0.3) + (posse_bola * 0.15) + (passes_eficazes * 0.15) + (ataques * 0.1)

        return força_total

    # Calcular a força base dos times
    força_casa = força(time_casa)
    força_fora = força(time_fora)

    # Aplicar bônus corretamente (+2% se for estrela, +2% se for mandante, máximo de 4%)
    bonus_casa = 1.0
    if time_casa['stars']:
        bonus_casa += 0.02  # +2% por ser estrela
    bonus_casa += 0.02  # +2% por jogar em casa
    bonus_casa = min(bonus_casa, 1.04)  # Garante que não passe de 4%

    # Aplicar bônus na força do time da casa
    força_casa *= bonus_casa

    # Calcular probabilidades
    total_força = força_casa + força_fora
    prob_casa = força_casa / total_força
    prob_fora = força_fora / total_força

    # Probabilidade de empate com base no equilíbrio dos times
    diff = abs(prob_casa - prob_fora)
    empate = max(0.05, 0.4 - (diff * 2))  # Ajuste para empate baseado na diferença

    # Ajuste final para garantir soma de 100%
    total = prob_casa + prob_fora + empate
    prob_casa = (prob_casa / total) * 100
    prob_fora = (prob_fora / total) * 100
    empate = (empate / total) * 100

    return {
        'vitória_time_casa': round(prob_casa, 2),
        'empate': round(empate, 2),
        'vitória_time_fora': round(prob_fora, 2),
    }

# Exemplo de uso:
partida = {
    'homeMach': 'Arsenal',
    'visitingTeam': 'Barcelona'
}

resultado = calcular_probabilidades(partida)
print(resultado)



os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/ymendes/projects/converter-backend/credenciais_bigquery.json"
 
load_dotenv() 
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
# client = bigquery.Client()

@app.route('/get-all-crime', methods=['GET'])
def getAllCrime():
  name = request.args.get('name')
  limit = request.args.get('limit')

  if not name:
    return jsonify({"error": "A propriedade 'name' é obrigatória" }), 400

  try:
    limit = int(limit)
  except:
    return jsonify({"error": "O 'limit' deve ser um número inteiro." })

  if limit < 1 or limit > 10:
    return jsonify({"error": "O limite deve ser entre 1 e 10"}), 400

  try:
    query = f"""
    SELECT primary_type, case_number
    FROM `bigquery-public-data.chicago_crime.crime`
    WHERE  primary_type = '{name}'
    LIMIT {limit}
    """

    df = client.query(query).to_dataframe()
    if df.empty:
      return jsonify({"error": "Nenhum crime encontrado com o nome especificado."}), 404

    return jsonify(df.to_dict(orient="records")), 200
  
  except Exception as e:
    print(f"Erro: {e}")
    return jsonify({"error": str(e)}), 500

@app.route('/get-all-distinct', methods=['GET'])
def getAllCrime_distinct():
  
  try:
    query = f"""
    SELECT DISTINCT primary_type
    FROM `bigquery-public-data.chicago_crime.crime`
    ORDER BY primary_type
    LIMIT 20
    """

    df = client.query(query).to_dataframe()    
    return jsonify(df.to_dict(orient="records")), 200
  
  except Exception as e:
    print(f"Erro: {e}")
    return jsonify({"error": str(e)}), 500

@app.route('/get-all-count', methods=['GET'])
def getAllCrime_count():
  name = request.args.get('name')
  try:
    query = f"""
    SELECT primary_type, COUNT(*) AS total_casos
    FROM `bigquery-public-data.chicago_crime.crime`
    WHERE primary_type = '{name}'
    GROUP BY primary_type
    ORDER BY total_casos DESC
    LIMIT 20
    """

    df = client.query(query).to_dataframe()  
    return jsonify(df.to_dict(orient="records")), 200
  
  except Exception as e:
    print(f"Erro: {e}")
    return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
  app.run(debug=True)