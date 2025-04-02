from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import pandas as pd
from flask_cors import CORS

attributesImportance = {
  'goalsScored': 2,
  'goalsConceded': -1.40,
  'wins': 1,
  'draws': 0.50,
  'defeats': -1,
  'ballPossesion': 0.80,
  'passingEffectiveness': 0.45,
  'attacks': 0.10,
}


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
        'name': 'PSG',
        'id': '1',
        'stars': False,
        'goalsScored': 25,
        'goalsConceded': 10,
        'wins': 7,
        'draws': 1,
        'defeats': 4,
        'ballPossesion': 60.34,
        'passingEffectiveness': 89.50,
        'attacks': 776,
      },
      {
        'name': 'Internazionale',
        'id': '3',
        'stars': False,
        'goalsScored': 15,
        'goalsConceded': 2,
        'wins': 8,
        'draws': 1,
        'defeats': 1,
        'ballPossesion': 50.20,
        'passingEffectiveness': 88.30,
        'attacks': 338,
      },
      {
        'name': 'Bayern München',
        'id': '6',
        'stars': True,
        'goalsScored': 28,
        'goalsConceded': 14,
        'wins': 8,
        'draws': 1,
        'defeats': 3,
        'ballPossesion': 61.92,
        'passingEffectiveness': 88.92,
        'attacks': 758,
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

def searchTeam(teamName):
    for league in leagues:
        for team in league['teams']:
            if team['name'] == teamName:
                return team
    return None

def generatePower(team, attributesImportance):
  total_power = 0
  
  for key in team:
    if key in attributesImportance:
      total_power += team[key] * attributesImportance[key]
    
  if team.get('stars', False):
      total_power *= 1.02  # Aumento de 2% Se o time for um time estrela
  
  return total_power

def calculate_match_probabilities(homeTeamPower, visitingTeamPower):
	# Calculando a soma dos poderes dos dois times
	total_power = homeTeamPower + visitingTeamPower
	
	# A diferença de poder entre os times
	power_difference = abs(homeTeamPower - visitingTeamPower)
	
	# Quanto menor a diferença, maior a chance de empate
	draw_prob = max(0.2, (1 - power_difference / total_power) * 0.4)  # Empate entre 20% e 50%

	# Calculando as probabilidades de vitória dos times
	home_win_prob = homeTeamPower / total_power * (1 - draw_prob)
	visiting_win_prob = visitingTeamPower / total_power * (1 - draw_prob)
	
	# Convertendo as probabilidades para percentuais
	home_win_prob *= 100
	visiting_win_prob *= 100
	draw_prob *= 100
	
	# Normalizando as probabilidades para garantir que somem 100%
	total_prob = home_win_prob + visiting_win_prob + draw_prob
	
	# Normalizando para que a soma das probabilidades seja 100%
	home_win_prob = round((home_win_prob / total_prob) * 100, 2)
	draw_prob = round((draw_prob / total_prob) * 100, 2)
	visiting_win_prob = round((visiting_win_prob / total_prob) * 100, 2)
	
	return {
		'home_win_prob': home_win_prob,
		'draw_prob': draw_prob,
		'visiting_win_prob': visiting_win_prob
	}


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/ymendes/projects/converter-backend/credenciais_bigquery.json"
 
load_dotenv() 
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
# client = bigquery.Client()

@app.route('/best/<teamProp>', methods=['GET'])
def get_best_teams(teamProp):
	teams = [team for league in leagues for team in league['teams']]
    
	if teamProp == 'power':
		for team in teams:
			team['power'] = generatePower(team, attributesImportance)
    
	if not all(teamProp in team for team in teams):
			return jsonify({'error': 'Propriedade inválida'}), 400
	
	is_defense_stat = teamProp == 'goalsConceded'
	sorted_teams = sorted(teams, key=lambda x: x[teamProp], reverse=not is_defense_stat)
	
	return jsonify([
			{'id': team['id'], 'name': team['name'], 'value': team[teamProp]}
			for team in sorted_teams
	])

@app.route('/teams', methods=['GET'])
def list_teams():
  all_teams = [{'id': team['id'], 'name': team['name']} for league in leagues for team in league['teams']]
  return jsonify(all_teams)

@app.route('/match-analysis', methods=['POST'])
def createMatchAnalysis():
  data = request.json

  homeTeam = searchTeam(data['homeTeam'])
  visitingTeam = searchTeam(data['visitingTeam'])

  if not homeTeam or not visitingTeam:
    return jsonify({"error": "Um dos times não foi encontrado"}), 404

  powerHomeTeam = generatePower(homeTeam, attributesImportance) * 1.02
  powerVisitingTeam = generatePower(visitingTeam, attributesImportance)

  result = calculate_match_probabilities(powerHomeTeam, powerVisitingTeam)

  return jsonify(result), 200
  


if __name__ == '__main__':
  app.run(debug=True)