"""
Program to generate relevant stats based on League of Legends match history, especially about win rates.

TO DO:
- Compile stats from challenger league
- Use stats to determine role
- Combine generate and update match history functions
- Fix if logic
- Add optional parameter region to match history
"""

import cassiopeia
import json
import re
from league_match_history import LeagueHistory
import misc
from match_analysis import MatchAnalysis
from summoner import Summoner

# Main method

if __name__ == "__main__":
    '''
    cass = cassiopeia
    cass.set_riot_api_key('s')
    print(cass.get_summoner(name='mintyorange', region= 'NA').id)
    '''
    cass = misc.create_cassiopeia()

    # mintyorange = Summoner(cass, summoner_data=['mintyorange', 'NA'])
    # mintyorange.get_match_history(5)

    league_matchlist = LeagueHistory('NA', 'GOLD', 'I', 500)
    match_analysis = MatchAnalysis(league_matchlist.league_history, 'GOLD1')
    match_analysis.get_position_data()
    match_analysis.set_champion_position(10)
