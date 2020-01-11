import json
import os
from os import path
import cassiopeia
import threading
import text_colors
import inflect
import operator
import re
import datapipelines
import misc
from queue import Queue


class MatchHistory:
    def __init__(self, summoner_name=None):
        if not path.exists("summoner_data"):
            os.mkdir("summoner_data")
        if not path.exists("summoner_matchlists"):
            os.mkdir("summoner_matchlists")

        if path.exists('champion_positions.json'):
            with open('champion_positions.json', encoding='utf8') as json_file:
                self.champion_positions = json.load(json_file)
        else:
            self.champion_positions = self.generate_champion_position_file()
        self.new_user = False
        if summoner_name is not None:
            self.summoner_filepath = misc.get_filepath(summoner_name.lower(), outside_dir="summoner_data",
                                                       file_suffix="data.json")
            if path.exists(self.summoner_filepath):
                text_colors.print_log("Summoner file located.")
                with open(self.summoner_filepath, encoding='utf8') as json_file:
                    self.summoner_data = json.load(json_file)
            else:
                text_colors.print_error("Summoner file \"" + self.summoner_filepath + "\" not found.")
                text_colors.print_log("Creating new user profile...")
                self.new_user = True
                self.summoner_data = {
                    "username": "",
                    "region": ""
                }
                self.summoner_filepath = ""
        if summoner_name is None:
            text_colors.print_log("Creating new user profile...")
            self.new_user = True
            self.summoner_data = {
                "username": "",
                "region": ""
            }
            self.summoner_filepath = ""

        if path.exists("api_key.txt"):
            with open("api_key.txt", 'r') as api_key:
                self.api_key = api_key.readline()
        else:
            self.api_key = ""

            # if path.exists("position_data.json"):
            # with open('position_data.json', encoding='utf8') as json_file:
            # self.position_data = json.load(json_file)
        # else:
        self.position_data = self.generate_position_data_file()
        self.regions = ["RU", 'KR', 'BR', 'OCE', 'JP', 'NA', 'EUNE', 'EUW', 'TR', 'LAN', 'LAS']
        self.p = inflect.engine()
        self.cass = cassiopeia
        self.summoner = self.get_summoner()
        self.matchlist_file = misc.get_filepath(self.summoner.name, "summoner_matchlists", "matchlist.json")
        if path.exists(self.matchlist_file):
            with open(self.matchlist_file, encoding='utf8') as json_file:
                self.match_history = json.load(json_file)

    def clean_wrong_positions(self):
        for match in self.match_history['Matches']:
            for player in ['Allies', 'Enemies']:
                if self.match_history['Matches'][match].get('Remake'):
                    continue
                roles = {
                    "TOP": 0,
                    "JUNGLE": 0,
                    "MIDDLE": 0,
                    "BOTTOM": 0,
                    "SUPPORT": 0,
                }
                participants = dict()
                participants.update(self.match_history['Matches'][match][player])
                for participant in participants.values():
                    if participant['Position'] != "UNKNOWN":
                        roles[participant['Position']] += 1
                for role in roles:
                    if roles[role] > 1:
                        for participant in participants:
                            if participants[participant]['Position'] == role:
                                self.match_history['Matches'][match][player][participant]['Position'] = "UNKNOWN"
        with open(self.matchlist_file, 'w') as outfile:
            json.dump(self.match_history, outfile)

    def generate_champion_position_file(self):
        champion_positions = {}
        for champion in misc.References.champions:
            champion_positions[champion] = ""
        with open('champion_positions.json', 'w') as outfile:
            json.dump(champion_positions, outfile)
        return champion_positions

    def generate_position_data_file(self):
        positions = {
            "TOP": 0,
            "JUNGLE": 0,
            "MIDDLE": 0,
            "BOTTOM": 0,
            "SUPPORT": 0,
            "Total": 0,
            "Percentages": {
                "TOP_%": 0.0,
                "JUNGLE_%": 0.0,
                "MIDDLE_%": 0.0,
                "BOTTOM_%": 0.0,
                "SUPPORT_%": 0.0,
            }
        }
        position_data = {}
        for champion in self.champion_positions:
            position_data[champion] = {}
            position_data[champion].update(positions)
        with open("position_data.json", 'w') as outfile:
            json.dump(position_data, outfile)
        return position_data

    def parse_champion_name(self, champion):
        champion_name = re.sub('[^A-Za-z0-9]+', '', champion).title()
        if champion_name == "Nunuwillump":
            champion_name = "Nunu"
        return champion_name

    def set_champion_positions(self):
        self.clean_wrong_positions()
        for match in self.match_history['Matches'].values():
            if match.get('Remake'):
                continue
            participants = dict()
            participants.update(match['Allies'])
            participants.update(match['Enemies'])
            for participant in participants.values():
                if participant['Position'] != "UNKNOWN":
                    champion_name = self.parse_champion_name(participant['Champion'])
                    self.position_data[champion_name][participant['Position']] += 1
                    self.position_data[champion_name]['Total'] += 1
        for champion in self.position_data:
            for role in ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "SUPPORT"]:
                percentage = misc.get_percentage(
                    self.position_data[champion][role],
                    self.position_data[champion]['Total'])
                self.position_data[champion]['Percentages'][role + '_%'] = percentage
            preferred_role = max(self.position_data[champion]['Percentages'].items(),
                                 key=operator.itemgetter(1))[0].strip('_%')
            self.champion_positions[champion] = preferred_role
        with open("champion.json", "w") as outfile:
            json.dump(self.champion_positions, outfile)
        with open("position_data.json", "w") as outfile:
            json.dump(self.position_data, outfile)

    def get_summoner(self):
        if self.api_key != "":
            text_colors.print_log("Using api key from summoner file...")
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

        if self.summoner_data['region'] == "":
            text_colors.print_log("Please enter your region:\nValid inputs include: " + ', '.join(self.regions))
            region = input().upper()
        else:
            region = self.summoner_data['region'].upper()
            text_colors.print_log("Using region \"" + region + "\" from summoner file...")
        while region not in self.regions:
            text_colors.print_error("Invalid region.")
            text_colors.print_log("Valid inputs include: " + ', '.join(self.regions))
            region = input().upper()
        self.summoner_data['region'] = region

        if self.summoner_data['username'] == "":
            text_colors.print_log("Please enter your summoner name:")
            username = input().upper()

        else:
            username = self.summoner_data['username'].lower()
            text_colors.print_log("Using username \"" + username + "\" from summoner file...")

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
        if self.new_user:
            self.summoner_filepath = misc.get_filepath(username.lower(), "summoner_data", "data.json")
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

    def get_position(self, lane, role, champion):
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
        elif lane == "NONE" and role == "DUO_SUPPORT":
            return "SUPPORT"
        else:
            return "UNKNOWN"

    def get_match_history(self, match_count):

        full_match_history = self.cass.get_match_history(self.summoner, queues={self.cass.data.Queue.ranked_solo_fives},
                                                         begin_index=match_count)
        match_history = {'Matches': {}}
        result = Queue()
        stop_thread = False
        update = False
        initial_len = 0
        if path.exists(self.matchlist_file):
            text_colors.print_log("Updating existing \"" + self.matchlist_file + "\"...")
            update = True
            match_history = json.load(open(self.matchlist_file, encoding="utf8"))
            initial_len = len(match_history['Matches'])
            match_thread = threading.Thread(target=self.update_match_history,
                                            args=(lambda: stop_thread, match_history, full_match_history, result))
        else:
            match_thread = threading.Thread(target=self.generate_match_history,
                                            args=(lambda: stop_thread, match_history, full_match_history, result))

        text_colors.print_log("Generating Match History (type \"stop\" to quit early)...")
        match_thread.start()
        while match_thread.is_alive():
            if input() == "stop":
                text_colors.print_log("Stopping after current match is recorded...")
                stop_thread = True
                match_thread.join()
                text_colors.print_log("Match History Creation Terminated.")
                break
        if not stop_thread:
            match_thread.join()
            text_colors.print_log("Match History Successfully Created.")

        with open(self.matchlist_file, 'w') as outfile:
            match_history = result.get()
            json.dump(match_history, outfile)

        if update:
            text_colors.print_log(
                "Successfully logged " + str(len(match_history['Matches'])) + " {matches} into file \"".format(
                    matches=self.p.plural("match", len(match_history['Matches']))) + self.matchlist_file + "\".")
            text_colors.print_log(
                str(len(match_history['Matches']) - initial_len) + " new %s recorded." % self.p.plural(
                    'match', (len(match_history['Matches'])) - initial_len))
        else:
            text_colors.print_log(
                "Successfully logged " + str(
                    len(match_history['Matches'])) +
                " {matches} into file \"".format(matches=self.p.plural('match', len(match_history['Matches']))) +
                self.matchlist_file + "\".")

    def add_match_data(self, match, match_history):
        if match.is_remake:
            text_colors.print_error("Logging remake match " + str(match.id))
            match_history['Matches'][match.id] = {'Remake': True}
            return match_history
        text_colors.print_log("Begin Recording Match " + str(match.id))
        user = [participant for participant in match.participants if participant.summoner.name == self.summoner.name][0]
        allies = [participant for participant in match.participants if participant.team == user.team]
        enemies = [participant for participant in match.participants if participant.team != user.team]
        match_history['Matches'][match.id] = {}
        match_history['Matches'][match.id]['Allies'] = {}
        for ally in allies:
            match_history['Matches'][match.id]['Allies'][ally.summoner.name] = {}
            match_history['Matches'][match.id]['Allies'][ally.summoner.name]['Champion'] = ally.champion.name
            match_history['Matches'][match.id]['Allies'][ally.summoner.name]['Lane'] = self.parse_lane(ally.lane)
            match_history['Matches'][match.id]['Allies'][ally.summoner.name]['Role'] = ally.role.name
            match_history['Matches'][match.id]['Allies'][ally.summoner.name]['Position'] = self.get_position(
                ally.lane, ally.role, ally.champion.name)
            match_history['Matches'][match.id]['Allies'][ally.summoner.name]['Kills'] = ally.stats.kills
            match_history['Matches'][match.id]['Allies'][ally.summoner.name]['Deaths'] = ally.stats.deaths
            match_history['Matches'][match.id]['Allies'][ally.summoner.name]['Assists'] = ally.stats.assists
            match_history['Matches'][match.id]['Allies'][ally.summoner.name]['KDA'] = round(ally.stats.kda, 2)
            match_history['Matches'][match.id]['Allies'][ally.summoner.name]['Victory'] = ally.stats.win

        match_history['Matches'][match.id]['Enemies'] = {}
        for enemy in enemies:
            match_history['Matches'][match.id]['Enemies'][enemy.summoner.name] = {}
            match_history['Matches'][match.id]['Enemies'][enemy.summoner.name]['Champion'] = enemy.champion.name
            match_history['Matches'][match.id]['Enemies'][enemy.summoner.name]['Lane'] = self.parse_lane(enemy.lane)
            match_history['Matches'][match.id]['Enemies'][enemy.summoner.name]['Role'] = enemy.role.name
            match_history['Matches'][match.id]['Enemies'][enemy.summoner.name]['Position'] = self.get_position(
                enemy.lane, enemy.role, enemy.champion.name)
            match_history['Matches'][match.id]['Enemies'][enemy.summoner.name]['Kills'] = enemy.stats.kills
            match_history['Matches'][match.id]['Enemies'][enemy.summoner.name]['Deaths'] = enemy.stats.deaths
            match_history['Matches'][match.id]['Enemies'][enemy.summoner.name]['Assists'] = enemy.stats.assists
            match_history['Matches'][match.id]['Enemies'][enemy.summoner.name]['KDA'] = round(enemy.stats.kda, 2)
            match_history['Matches'][match.id]['Enemies'][enemy.summoner.name]['Victory'] = enemy.stats.win
        return match_history

    def update_match_history(self, stop, match_history, full_match_history, result):
        for match in full_match_history:
            if match.id not in [int(key) for key in match_history['Matches'].keys()]:
                match_history = self.add_match_data(match, match_history)
            else:
                text_colors.print_error("Skipping logged match...")
            if stop():
                result.put(match_history)
                return None
        result.put(match_history)
        return None

    def generate_match_history(self, stop, match_history, full_match_history, result):
        for match in full_match_history:
            match_history = self.add_match_data(match, match_history)
            if stop():
                result.put(match_history)
                return None
        result.put(match_history)
        return None
