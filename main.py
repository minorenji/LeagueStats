"""
Program to generate relevant stats based on League of Legends match history, especially about win rates.

TO DO:
- Compile stats from challenger league
- Use stats to determine role
- Combine generate and update match history functions
- Fix if logic
- Add optional parameter region to match history
"""
from match_history import MatchHistory
import cassiopeia
import json
import re

# Main method

if __name__ == "__main__":
    '''
    cass = cassiopeia
    cass.set_riot_api_key('s')
    print(cass.get_summoner(name='mintyorange', region= 'NA').id)
    '''
    matchlist = MatchHistory("shadowviolinist")
    matchlist.get_match_history(1)
    # matchlist.set_champion_positions()
