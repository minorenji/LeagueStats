import os
import json
import re
import cassiopeia
import text_colors


def get_percentage(value, total):
    if total == 0:
        return 0.00
    else:
        return round(value / total, 2) * 100


def makedir(path):
    if not os.path.exists(path):
        os.mkdir(path)


def conditional_open(path):
    if os.path.exists(path):
        with open(path, 'r') as text:
            return text.readline()
    else:
        return None


def create_cassiopeia():
    cass = cassiopeia
    set_api_key(cass)
    return cass


def set_api_key(cass: cassiopeia):
    api_key = conditional_open("api_key.txt")
    if api_key is not None:
        text_colors.print_log("Using api key from file...")
        cass.set_riot_api_key(api_key)
    else:
        text_colors.print_error("API key is missing. Please enter a valid API key:")
        api_key = input()
        cass.set_riot_api_key(api_key)
    result = None
    while result is None:
        try:
            result = cass.get_summoner(name='mintyorange', region='NA').id
            text_colors.print_log("API key verified.")

        except cassiopeia.datastores.riotapi.common.APIRequestError as err:
            if '403' in str(err):
                text_colors.print_error("API key is invalid. Please enter a valid API key:")
                api_key = input()
                cass.set_riot_api_key(api_key)
            else:
                raise


def conditional_open_json(path):
    if os.path.exists(path):
        with open(path, encoding='utf8') as json_file:
            return json.load(json_file)
    else:
        return None


def parse_champion_name(champion):
    champion_name = re.sub('[^A-Za-z0-9]+', '', champion).title()
    if champion_name == "Nunuwillump":
        champion_name = "Nunu"
    return champion_name


def get_filepath(filename, outside_dir=None, file_suffix=None, file_prefix=None):
    if file_suffix is not None:
        file_suffix = "_" + file_suffix
    else:
        file_suffix = ""
    if file_prefix is not None:
        file_prefix = file_suffix + "_"
    else:
        file_prefix = ""
    if outside_dir is not None:
        outside_dir = outside_dir + "/"
    else:
        outside_dir = ""
    filepath = "{outside_dir}{file_prefix}{filename}{file_suffix}".format(outside_dir=outside_dir,
                                                             filename=filename,
                                                             file_suffix=file_suffix, file_prefix=file_prefix)
    return filepath


class References:
    champions = ['Aatrox', 'Ahri', 'Akali', 'Alistar', 'Amumu', 'Anivia', 'Annie', 'Aphelios', 'Ashe', 'Aurelionsol',
                 'Azir', 'Bard', 'Blitzcrank', 'Brand', 'Braum', 'Caitlyn', 'Camille', 'Cassiopeia', 'Chogath', 'Corki',
                 'Darius', 'Diana', 'Draven', 'Drmundo', 'Ekko', 'Elise', 'Evelynn', 'Ezreal', 'Fiddlesticks', 'Fiora',
                 'Fizz', 'Galio', 'Gangplank', 'Garen', 'Gnar', 'Gragas', 'Graves', 'Hecarim', 'Heimerdinger', 'Illaoi',
                 'Irelia', 'Ivern', 'Janna', 'Jarvaniv', 'Jax', 'Jayce', 'Jhin', 'Jinx', 'Kaisa', 'Kalista', 'Karma',
                 'Karthus', 'Kassadin', 'Katarina', 'Kayle', 'Kayn', 'Kennen', 'Khazix', 'Kindred', 'Kled', 'Kogmaw',
                 'Leblanc', 'Leesin', 'Leona', 'Lissandra', 'Lucian', 'Lulu', 'Lux', 'Malphite', 'Malzahar', 'Maokai',
                 'Masteryi', 'Missfortune', 'Wukong', 'Mordekaiser', 'Morgana', 'Nami', 'Nasus', 'Nautilus', 'Neeko',
                 'Nidalee', 'Nocturne', 'Nunu', 'Olaf', 'Orianna', 'Ornn', 'Pantheon', 'Poppy', 'Pyke', 'Qiyana',
                 'Quinn', 'Rakan', 'Rammus', 'Reksai', 'Renekton', 'Rengar', 'Riven', 'Rumble', 'Ryze', 'Sejuani',
                 'Senna', 'Shaco', 'Shen', 'Shyvana', 'Singed', 'Sion', 'Sivir', 'Skarner', 'Sona', 'Soraka', 'Swain',
                 'Sylas', 'Syndra', 'Tahmkench', 'Taliyah', 'Talon', 'Taric', 'Teemo', 'Thresh', 'Tristana', 'Trundle',
                 'Tryndamere', 'Twistedfate', 'Twitch', 'Udyr', 'Urgot', 'Varus', 'Vayne', 'Veigar', 'Velkoz', 'Vi',
                 'Viktor', 'Vladimir', 'Volibear', 'Warwick', 'Xayah', 'Xerath', 'Xinzhao', 'Yasuo', 'Yorick', 'Yuumi',
                 'Zac', 'Zed', 'Ziggs', 'Zilean', 'Zoe', 'Zyra']
    regions = ["RU", 'KR', 'BR', 'OCE', 'JP', 'NA', 'EUNE', 'EUW', 'TR', 'LAN', 'LAS']
