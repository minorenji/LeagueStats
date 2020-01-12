import datapipelines
import inflect
import text_colors
import misc
import cassiopeia
import json
import match_history


class Summoner:
    def __init__(self, cass: cassiopeia, summoner_data: [] = None, summoner_filepath=None):
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
        self.cass = cass
        self.summoner = self.get_summoner()
        self.matchlist_file = misc.get_filepath(self.summoner.name, "summoner_matchlists", "matchlist.json")
        self.match_history = misc.conditional_open_json(self.matchlist_file)

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
            json.dump(self.summoner_data, outfile, indent=2)

        with open("api_key.txt", 'w') as outfile:
            outfile.write(self.api_key)

        return self.cass.get_summoner(name=username, region=region)

    def get_match_history(self, length):
        if self.match_history is None:
            text_colors.print_error("Matchlist file does not exist.")
            text_colors.print_log("Creating new file \"" + self.matchlist_file + "\"")
            self.match_history = {'Matches': {}}
        else:
            text_colors.print_log("Adding to file \"" + self.matchlist_file + "\"...")

        self.match_history = match_history.get_match_history(self.cass, False, self.match_history, summoner=self.summoner, length=length)

        with open(self.matchlist_file, 'w') as outfile:
            json.dump(self.match_history, outfile, indent=2 )