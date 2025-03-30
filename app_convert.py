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
        'name': 'Real Madrd',
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
      
    ],
  },
]

def calcular_probabilidades(time_casa, time_fora):
    def força(time):
        jogos = time['wins'] + time['draws'] + time['defeats']
        ataque = time['goalsScored'] / jogos
        defesa = (1 / (time['goalsConceded'] + 1))  # evitar divisão por zero
        return ataque * defesa

    # Força bruta dos dois times
    força_casa = força(time_casa)
    força_fora = força(time_fora)

    # Bônus se tiver stars ou estiver jogando em casa
    if time_casa['stars']:
        força_casa *= 1.1
    if time_fora['stars']:
        força_fora *= 1.1

    força_casa *= 1.1  # bônus por estar jogando em casa

    # Calcular chance de vitória proporcional à força
    total_força = força_casa + força_fora
    prob_casa = força_casa / total_força
    prob_fora = força_fora / total_força

    # Empate depende da proximidade das forças
    diff = abs(prob_casa - prob_fora)
    empate = max(0.1, 0.4 - diff)  # mais equilíbrio, mais chance de empate

    # Ajuste final para somar 1.0
    total = prob_casa + prob_fora + empate
    prob_casa = prob_casa / total
    prob_fora = prob_fora / total
    empate = empate / total

    return {
        'vitória_time_casa': round(prob_casa * 100, 2),
        'empate': round(empate * 100, 2),
        'vitória_time_fora': round(prob_fora * 100, 2),
    }


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/ymendes/projects/converter-backend/credenciais_bigquery.json"
 
load_dotenv() 
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
client = bigquery.Client()

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