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
        self.champion_positions = self.generate_champion_position_file()
        self.position_data = misc.conditional_open_json(self.path + '/position_data.json')

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
            "Total": 0
        }
        position_data = {}
        for champion in self.champion_positions:
            position_data[champion] = {}
            position_data[champion].update(positions)
        with open(self.path + "/position_data.json", 'w') as outfile:
            json.dump(position_data, outfile)
        return position_data

    def set_champion_position(self, min_matches):
        if self.position_data is None:
            text_colors.print_error("Position data file does not exist.")
            return None

        self.champion_positions = self.generate_champion_position_file()

        text_colors.print_log("Calculating most likely champion positions...")
        for champion_name, champion in self.position_data.items():
            champion['Percentages'] = {}
            for role in ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "SUPPORT"]:
                percentage = misc.get_percentage(
                    champion[role],
                    champion['Total'])
                champion['Percentages'][role + "_%"] = 0
                champion['Percentages'][role + "_%"] += percentage
            if champion['Total'] < min_matches:
                preferred_role = "UNKNOWN"
            else:
                preferred_role = max(champion['Percentages'].items(),
                                     key=operator.itemgetter(1))[0].strip('_%')
            self.champion_positions[champion_name] = preferred_role
            self.position_data[champion_name] = champion

        text_colors.print_log("Writing new data to file...")

        with open(self.path + "/champion_positions.json", "w") as outfile:
            json.dump(self.champion_positions, outfile, indent=2)

        with open(self.path + "/position_data.json", "w") as outfile:
            json.dump(self.position_data, outfile, indent=2)

    def get_position_data(self):
        self.position_data = self.generate_position_data_file()
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

        text_colors.print_log("Writing new data to file...")

        with open(self.path + "/position_data.json", "w") as outfile:
            json.dump(self.position_data, outfile)
