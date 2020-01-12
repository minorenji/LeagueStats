"""
Program to generate relevant stats based on League of Legends match history, especially about win rates.

TO DO:
- If match is already logged during league history generation, use next unlogged match in summoner's history
"""

import cassiopeia
import json
import re
from league_match_history import LeagueHistory
import misc
from match_analysis import MatchAnalysis
from summoner import Summoner

# Main function

if __name__ == "__main__":

    cass = misc.create_cassiopeia()

    # mintyorange = Summoner(cass, summoner_data=['mintyorange', 'NA'])
    # mintyorange.get_match_history(100)

    league_matchlist = LeagueHistory('NA', 'GOLD', 'I', 600)
    league_history = misc.conditional_open_json("league_matchlists/GOLD_I_league_matchlist.json")
    match_analysis = MatchAnalysis(league_history, 'GOLD1')
    match_analysis.get_position_data()
    match_analysis.set_champion_position(10)

