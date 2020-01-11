import match_history
import json
import misc
import cassiopeia
import text_colors
import inflect


class LeagueHistory(match_history.MatchHistory):
    def __init__(self, region, league, division, length: int):
        self.p = inflect.engine()
        self.league = league
        self.length = length
        self.division = division
        misc.makedir("league_matchlists")
        self.filepath = misc.get_filepath("{league}_{division}".format(league=league, division=division),
                                          "league_matchlists", "league_matchlist.json")
        self.region = region.upper()
        self.api_key = misc.conditional_open("api_key.txt")
        self.cass = cassiopeia
        self.verify_api_key()
        self.league_list = cassiopeia.core.league.LeagueEntries(region=region, tier=league,
                                                                queue=self.cass.data.Queue.ranked_solo_fives,
                                                                division=division)
        self.league_history = misc.conditional_open_json(self.filepath)
        if self.league_history is None:
            self.league_history = {'Matches': {}}
        with open(self.filepath, 'w') as outfile:
            json.dump(self.league_history, outfile)
        self.generate_league_history()
        self.league_history = misc.conditional_open_json(self.filepath)

    def generate_league_history(self):
        length = len(self.league_history['Matches'])
        for entry in self.league_list:
            '''
            stop = input()
            if stop == 'stop':
                exit("League matchlist of length " + str(length) + " created.")
            '''
            if length == self.length:
                break
            text_colors.print_log("Adding match of summoner \"" + entry.summoner.name + "\"...")
            self.get_match_history(summoner=entry.summoner, match_count=1, filepath=self.filepath)
            length += 1
