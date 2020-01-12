import concurrent.futures

import cassiopeia
import inflect
import misc
import time

import text_colors
import keyboard

p = inflect.engine()


def clean_wrong_positions(match_history):
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
    return match_history


def parse_lane(lane):
    if lane is None:
        lane = "NONE"
    else:
        lane = lane.name.upper()
    return lane


def get_position(lane, role):
    lane = parse_lane(lane)
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


stop_thread = False


def get_match_history(cass: cassiopeia, league_history: bool, match_history, summoner, length,
                      logged=None):
    global stop_thread
    full_match_history = cass.get_match_history(summoner, queues={cass.data.Queue.ranked_solo_fives}, end_index=100)

    initial_len = len(match_history['Matches'])
    if initial_len == length and not league_history:
        text_colors.print_error("File already contains {} matches!".format(length))
        return match_history
    with concurrent.futures.ThreadPoolExecutor() as executor:
        match_thread = executor.submit(generate_match_history, match_history,
                                       full_match_history, league_history, length=length, logged=logged)
    match_history = match_thread.result()
    if not league_history:
        text_colors.print_log("Match history successfully generated.")
        text_colors.print_log(
            "Successfully logged " + str(len(match_history['Matches'])) + " {matches}.".format(
                matches=p.plural("match", len(match_history['Matches']))))
        text_colors.print_log(
            str(len(match_history['Matches']) - initial_len) + " new %s recorded." % p.plural(
                'match', (len(match_history['Matches'])) - initial_len))
    match_history = clean_wrong_positions(match_history)
    return match_history


def add_match_data(match, match_history):
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
            'Lane': parse_lane(participant.lane),
            'Role': participant.role.name.upper(),
            'Position': get_position(participant.lane, participant.role),
            'Kills': participant.stats.kills,
            'Deaths': participant.stats.deaths,
            'Assists': participant.stats.assists,
            'KDA': round(participant.stats.kda, 2),
            'Victory': participant.stats.win
        })
    return match_history


def generate_match_history(match_history, full_match_history, league_history, length, logged: [bool] = None):
    global stop_thread
    current_length = len(match_history['Matches'])
    if not league_history:
        match_no = current_length + 1
        text_colors.print_log("Generating match history...")
        text_colors.print_log("Hold \"ctrl + \\\" to end early...")
    else:
        current_length = 0
        match_no = 0
    match_gen = (match for match in full_match_history)
    while current_length != length:
        try:
            match = next(match_gen)
        except:
            return match_history
        if match.id not in [int(key) for key in match_history['Matches'].keys()]:
            if not league_history:
                text_colors.print_log(
                    "Begin recording match " + str(match_no) + " of " + str(length) + "...")
            else:
                text_colors.print_log("Recording match ID: " + str(match.id))
            match_history = add_match_data(match, match_history)
            current_length += 1
            match_no += 1
        else:
            text_colors.print_error("Skipping logged match ID {match_id}...".format(match_id=match.id))
        half_second = time.time() + 0.5
        if not league_history:
            print("=" * 50)
            while time.time() < half_second:
                if keyboard.is_pressed('ctrl+\\'):
                    text_colors.print_log("Terminating match history generation...")
                    return match_history
    return match_history
