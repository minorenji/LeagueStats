def get_percentage(value, total):
    return round(value / total, 2) * 100


def get_filepath(filename, outside_dir=None, file_suffix=None):
    if file_suffix is not None:
        file_suffix = "_" + file_suffix
    else:
        file_suffix = ""
    if outside_dir is not None:
        outside_dir = outside_dir + "/"
    else:
        outside_dir = ""
    filepath = "{outside_dir}{filename}{file_suffix}".format(outside_dir=outside_dir,
                                                             filename=filename,
                                                             file_suffix=file_suffix)
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
