import misc
import os
import json
import operator
import text_colors


class MatchAnalysis:
    def __init__(self, matchlist, name):
        self.name = name
        self.matchlist = matchlist
        misc.makedir("MatchAnalyses")
        misc.makedir("MatchAnalyses/" + name)
        self.path = "MatchAnalyses/" + name
        self.champion_positions = misc.conditional_open_json(self.path + '/champion_positions.json')
        self.champion_positions = self.generate_champion_position_file()
        self.position_data = misc.conditional_open_json(self.path + '/position_data.json')
        if self.position_data is None:
            self.position_data = self.generate_position_data_file()

    def generate_champion_position_file(self):
        champion_positions = {}
        for champion in misc.References.champions:
            champion_positions[champion] = ""
        with open(self.path + '/champion_positions.json', 'w') as outfile:
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
        with open(self.path + "/position_data.json", 'w') as outfile:
            json.dump(position_data, outfile)
        return position_data

    def set_champion_positions(self):
        text_colors.print_log("Begin pulling champion data from matchlist \"" + self.name + "\".")
        match_no = 1
        for match in self.matchlist['Matches'].values():
            text_colors.print_log(
                "Scanning match " + str(match_no) + " of " + str(len(self.matchlist['Matches'])) + "...")
            if match.get('Remake'):
                continue
            participants = dict()
            participants.update(match['Blue Team'])
            participants.update(match['Red Team'])
            for participant in participants.values():
                if participant['Position'] != "UNKNOWN":
                    champion_name = misc.parse_champion_name(participant['Champion'])
                    self.position_data[champion_name][participant['Position']] += 1
                    self.position_data[champion_name]['Total'] += 1
            match_no += 1
        text_colors.print_log("Calculating most likely champion positions...")
        for champion in self.position_data:
            for role in ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "SUPPORT"]:
                percentage = misc.get_percentage(
                    self.position_data[champion][role],
                    self.position_data[champion]['Total'])
                self.position_data[champion]['Percentages'][role + '_%'] = percentage
            preferred_role = max(self.position_data[champion]['Percentages'].items(),
                                 key=operator.itemgetter(1))[0].strip('_%')
            self.champion_positions[champion] = preferred_role
        text_colors.print_log("Writing new data to files...")
        with open(self.path + "/champion_positions.json", "w") as outfile:
            json.dump(self.champion_positions, outfile)
        with open(self.path + "/position_data.json", "w") as outfile:
            json.dump(self.position_data, outfile)
