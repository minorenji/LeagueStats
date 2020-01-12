import match_history
import json
import misc
import cassiopeia
import text_colors
import inflect
import concurrent.futures
import keyboard
import time


class LeagueHistory:
    def __init__(self, region, league, division, length: int):
        self.length = 0
        self.p = inflect.engine()
        self.league = league
        self.full_length = length
        self.division = division
        misc.makedir("league_matchlists")
        self.filepath = misc.get_filepath("{league}_{division}".format(league=league, division=division),
                                          "league_matchlists", "league_matchlist.json")
        self.region = region.upper()
        self.api_key = misc.conditional_open("api_key.txt")
        self.cass = cassiopeia
        misc.set_api_key(self.cass)
        self.league_list = cassiopeia.core.league.LeagueEntries(region=region, tier=league,
                                                                queue=self.cass.data.Queue.ranked_solo_fives,
                                                                division=division)
        self.league_history = None
        self.get_league_history()

    def get_league_history(self):
        self.league_history = misc.conditional_open_json(self.filepath)
        if self.league_history is None:
            text_colors.print_error("Matchlist file does not exist.")
            text_colors.print_log("Creating new file \"" + self.filepath + "\"")
            self.league_history = {'Matches': {}}
        else:
            text_colors.print_log("Adding to file \"" + self.filepath + "\"...")
        initial_len = len(self.league_history['Matches'])
        stop_thread = False
        text_colors.print_log("Begin creating league history (Hold \"ctrl + \\\" to stop early)...")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            match_thread = executor.submit(self.generate_league_history)
        self.league_history = match_thread.result()
        with open(self.filepath, 'w') as outfile:
            json.dump(self.league_history, outfile)
        text_colors.print_log("League history file generated.")
        text_colors.print_log(
            "Successfully logged " + str(len(self.league_history['Matches'])) + " {matches} into file \"".format(
                matches=self.p.plural("match", len(self.league_history['Matches']))) + self.filepath + "\".")
        text_colors.print_log(
            str(len(self.league_history['Matches']) - initial_len) + " new %s recorded." % self.p.plural(
                'match', (len(self.league_history['Matches'])) - initial_len))

    def generate_league_history(self):
        league_history = self.league_history
        logged = [False]
        self.length = len(self.league_history['Matches'])
        if self.length == self.full_length:
            text_colors.print_error("Length of current league matchlist is already at length!")
            return league_history
        entry_gen = (entry for entry in self.league_list)
        while self.length < self.full_length:
            try:
                entry = next(entry_gen)
            except:
                text_colors.print_error(
                    "Encountered unexpected error while calling Riot API.\nTerminating matchlist creation")
                return league_history

            text_colors.print_log(
                "Adding match of summoner \"" + entry.summoner.name + "\" (match {} of {})...".format(self.length,
                                                                                                      self.full_length))
            league_history = match_history.get_match_history(summoner=entry.summoner, cass=self.cass,
                                                             league_history=True, length=1,
                                                             match_history=self.league_history)
            self.length += 1
            half_second = time.time() + 0.5
            print("=" * 50)
            while time.time() < half_second:
                if keyboard.is_pressed('ctrl+\\'):
                    text_colors.print_log("Terminating league history generation...")
                    return league_history
        return league_history
