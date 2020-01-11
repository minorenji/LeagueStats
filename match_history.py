import json
from queue import Queue
import concurrent.futures

import cassiopeia
import datapipelines
import inflect

import misc
import text_colors


class MatchHistory:
    def __init__(self, summoner_data: [] = None, summoner_filepath=None):
        if summoner_filepath is not None:
            self.summoner_data = misc.conditional_open_json(summoner_filepath)
            if self.summoner_data is None:
                raise TypeError(summoner_filepath + "does not exist.")
        elif summoner_data is not None:
            self.summoner_data = {
                "username": summoner_data[0],
                "region": summoner_data[1]
            }

            if len(summoner_data) != 2:
                raise TypeError("Argument \"summoner_data\" must be in form [summoner_name, region]")
        else:
            text_colors.print_log("Creating new user profile...")
            self.summoner_data = None
        self.summoner_filepath = None
        misc.makedir("summoner_data")
        misc.makedir("summoner_matchlists")

        self.api_key = misc.conditional_open("api_key.txt")

        self.p = inflect.engine()
        self.cass = cassiopeia
        self.verify_api_key()
        self.summoner = self.get_summoner()
        self.matchlist_file = misc.get_filepath(self.summoner.name, "summoner_matchlists", "matchlist.json")

    def clean_wrong_positions(self, match_history, filepath):
        for match in match_history['Matches']:
            for team in ['Blue Team', 'Red Team']:
                if match_history['Matches'][match].get('Remake'):
                    continue
                roles = {
                    "TOP": 0,
                    "JUNGLE": 0,
                    "MIDDLE": 0,
                    "BOTTOM": 0,
                    "SUPPORT": 0,
                }
                participants = dict()
                participants.update(match_history['Matches'][match][team])
                for participant in participants.values():
                    if participant['Position'] != "UNKNOWN":
                        roles[participant['Position']] += 1
                for role in roles:
                    if roles[role] > 1:
                        for participant in participants:
                            if participants[participant]['Position'] == role:
                                match_history['Matches'][match][team][participant]['Position'] = "UNKNOWN"
        with open(filepath, 'w') as outfile:
            json.dump(match_history, outfile)

    def verify_api_key(self):
        if self.api_key is not None:
            text_colors.print_log("Using api key from file...")
            self.cass.set_riot_api_key(self.api_key)
        else:
            text_colors.print_error("API key is missing. Please enter a valid API key:")
            self.api_key = input()
            self.cass.set_riot_api_key(self.api_key)
        result = None
        while result is None:
            try:
                result = self.cass.get_summoner(name='mintyorange', region='NA').id
                text_colors.print_log("API key verified.")

            except cassiopeia.datastores.riotapi.common.APIRequestError as err:
                if '403' in str(err):
                    text_colors.print_error("API key is invalid. Please enter a valid API key:")
                    self.api_key = input()
                    self.cass.set_riot_api_key(self.api_key)
                else:
                    raise

    def get_summoner(self):
        if self.summoner_data is None:
            text_colors.print_log(
                "Please enter your region:\nValid inputs include: " + ', '.join(misc.References.regions))
            region = input().upper()
            text_colors.print_log("Please enter your summoner name:")
            username = input().lower()
            self.summoner_data = {
                "username": "",
                "region": ""
            }

        else:
            region = self.summoner_data['region'].upper()
            username = self.summoner_data['username']
            text_colors.print_log("Using region \"" + region + "\" and \"" + username + "\"...")

        while region not in misc.References.regions:
            text_colors.print_error("Invalid region.")
            text_colors.print_log("Valid inputs include: " + ', '.join(misc.References.regions))
            region = input().upper()

        result = None
        while result is None:
            try:
                result = self.cass.get_summoner(name=username, region=region).id
                text_colors.print_log("Summoner found.")
            except (cassiopeia.datastores.riotapi.common.APIRequestError, datapipelines.common.NotFoundError) as err:
                if '404' in str(err) or 'No source' in str(err):
                    text_colors.print_error("Summoner of that name not found. Please enter a valid summoner name:")
                    self.api_key = input()
                    self.cass.set_riot_api_key(self.api_key)
                else:
                    raise
        self.summoner_data['username'] = username
        self.summoner_data['region'] = region
        self.summoner_filepath = misc.get_filepath(self.summoner_data['username'], "summoner_data", "data.json")
        with open(self.summoner_filepath, 'w') as outfile:
            json.dump(self.summoner_data, outfile)
        with open("api_key.txt", 'w') as outfile:
            outfile.write(self.api_key)
        return self.cass.get_summoner(name=username, region=region)

    def parse_lane(self, lane):
        if lane is None:
            lane = "NONE"
        else:
            lane = lane.name.upper()
        return lane

    def get_position(self, lane, role):
        lane = self.parse_lane(lane)
        role = role.name.upper()
        if lane == "MID_LANE" and role == "SOLO":
            return "MIDDLE"
        elif lane == "TOP_LANE" and role == "SOLO":
            return "TOP"
        elif lane == "JUNGLE" and role == "NONE":
            return "JUNGLE"
        elif lane == "BOT_LANE" and role == "DUO_CARRY":
            return "BOTTOM"
        elif lane == "BOT_LANE" and role == "DUO_SUPPORT":
            return "SUPPORT"
        else:
            return "UNKNOWN"

    def get_match_history(self, match_count, filepath=None, summoner=None):
        if filepath is None:
            filepath = self.matchlist_file
        if summoner is None:
            summoner = self.summoner
        full_match_history = self.cass.get_match_history(summoner, queues={self.cass.data.Queue.ranked_solo_fives},
                                                         begin_index=0, end_index=match_count)

        result = Queue()
        stop_thread = False
        initial_len = 0
        match_history = misc.conditional_open_json(filepath)

        if match_history is not None:
            text_colors.print_log("Updating existing \"" + filepath + "\"...")
            initial_len = len(match_history['Matches'])
        else:
            match_history = {'Matches': {}}
        text_colors.print_log("Generating match history (type \"stop\" to quit early)...")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            match_thread = executor.submit(self.generate_match_history, lambda: stop_thread, match_history,
                                           full_match_history)

        while match_thread.running():
            if input() == "stop":
                text_colors.print_log("Stopping after current match is recorded...")
                stop_thread = True
                text_colors.print_log("Match history creation terminated.")
                break
            elif match_thread.done():
                break

        text_colors.print_log("Match history successfully generated.")

        with open(filepath, 'w') as outfile:
            match_history = match_thread.result()
            json.dump(match_history, outfile)
        text_colors.print_log(
            "Successfully logged " + str(len(match_history['Matches'])) + " {matches} into file \"".format(
                matches=self.p.plural("match", len(match_history['Matches']))) + filepath + "\".")
        text_colors.print_log(
            str(len(match_history['Matches']) - initial_len) + " new %s recorded." % self.p.plural(
                'match', (len(match_history['Matches'])) - initial_len))

        self.clean_wrong_positions(match_history, filepath)

    def add_match_data(self, match, match_history):
        if match.is_remake:
            text_colors.print_error("Logging match as remake...")
            match_history['Matches'][match.id] = {'Remake': True}
            return match_history
        participants = [participant for participant in match.participants]
        match_history['Matches'][match.id] = {}
        match_history['Matches'][match.id]['Blue Team'] = {}
        match_history['Matches'][match.id]['Red Team'] = {}
        for participant in participants:
            if participant.team == match.blue_team:
                key = 'Blue Team'
            else:
                key = 'Red Team'
            match_history['Matches'][match.id][key][participant.summoner.name] = {}
            match_history['Matches'][match.id][key][participant.summoner.name].update({
                'Champion': participant.champion.name,
                'Lane': self.parse_lane(participant.lane),
                'Role': participant.role.name.upper(),
                'Position': self.get_position(participant.lane, participant.role),
                'Kills': participant.stats.kills,
                'Deaths': participant.stats.deaths,
                'Assists': participant.stats.assists,
                'KDA': round(participant.stats.kda, 2),
                'Victory': participant.stats.win
            })
            '''
            match_history['Matches'][match.id][key][participant.summoner.name] = {}
            match_history['Matches'][match.id][key][participant.summoner.name]['Champion'] = participant.champion.name
            match_history['Matches'][match.id][key][participant.summoner.name]['Lane'] = self.parse_lane(
                participant.lane)
            match_history['Matches'][match.id][key][participant.summoner.name]['Role'] = participant.role.name
            match_history['Matches'][match.id][key][participant.summoner.name]['Position'] = self.get_position(
                participant.lane, participant.role)
            match_history['Matches'][match.id][key][participant.summoner.name]['Kills'] = participant.stats.kills
            match_history['Matches'][match.id][key][participant.summoner.name]['Deaths'] = participant.stats.deaths
            match_history['Matches'][match.id][key][participant.summoner.name]['Assists'] = participant.stats.assists
            match_history['Matches'][match.id][key][participant.summoner.name]['KDA'] = round(participant.stats.kda, 2)
            match_history['Matches'][match.id][key][participant.summoner.name]['Victory'] = participant.stats.win
            '''
        return match_history

    def generate_match_history(self, stop, match_history, full_match_history):
        match_no = 1
        for match in full_match_history:
            if match.id not in [int(key) for key in match_history['Matches'].keys()]:
                text_colors.print_log(
                    "Begin recording match " + str(match_no) + " of " + str(len(full_match_history)) + "...")
                match_history = self.add_match_data(match, match_history)
            else:
                text_colors.print_error("Skipping logged match...")
            match_no += 1
            if stop():
                break
        return match_history
