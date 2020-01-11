import match_history
import json

class LeagueHistory(match_history.MatchHistory):
    def __init__(self):
        with open('champion.json', encoding='utf8') as json_file:
            self.champion_positions = json.load(json_file)
        with open('summoner_data.json', encoding='utf8') as json_file:
            self.summoner_data = json.load(json_file)
        if path.exists("matchlist.json"):
            with open('matchlist.json', encoding='utf8') as json_file:
                self.match_history = json.load(json_file)

        #if path.exists("position_data.json"):
            #with open('position_data.json', encoding='utf8') as json_file:
                #self.position_data = json.load(json_file)
        #else:
        self.position_data = self.generate_position_data_file()
        self.regions = ["RU", 'KR', 'BR', 'OCE', 'JP', 'NA', 'EUNE', 'EUW', 'TR', 'LAN', 'LAS']
        self.p = inflect.engine()
        self.cass = cassiopeia
        self.api_key = ''
        self.summoner = self.get_summoner()
        self.full_match_history = self.cass.get_match_history(self.summoner, queues={self.cass.data.Queue.ranked_solo_fives},
                                                    seasons={self.cass.data.Season.preseason_9, self.cass.Season.season_9})