import concurrent.futures

import cassiopeia
import inflect
import keyboard

import text_colors

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


def get_match_history(cass: cassiopeia, league_history: bool, match_history, summoner, length,
                      logged=None):
    full_match_history = cass.get_match_history(summoner, queues={cass.data.Queue.ranked_solo_fives})
    stop_thread = False

    initial_len = len(match_history['Matches'])
    if initial_len == length:
        text_colors.print_error("File already contains {} matches!".format(length))
        return match_history
    with concurrent.futures.ThreadPoolExecutor() as executor:
        match_thread = executor.submit(generate_match_history, match_history,
                                       full_match_history, league_history, stop=lambda: stop_thread, length=length, logged=logged)
        if not league_history:
            while match_thread.running():
                if keyboard.is_pressed('shift+`'):
                    text_colors.print_log("Stopping after current match is recorded...")
                    stop_thread = True
                    break
                elif match_thread.done():
                    break

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


def generate_match_history(match_history, full_match_history, league_history, length, stop=None, logged: [bool] = None):
    current_length = len(match_history['Matches'])
    if not league_history:
        match_no = current_length + 1
        text_colors.print_log("Generating match history...")
        text_colors.print_log("Press \"~\" to end early...")
    else:
        current_length = 0
        match_no = 0
    for match in full_match_history:
        if current_length == length:
            break
        if match.id not in [int(key) for key in match_history['Matches'].keys()]:
            if not league_history:
                text_colors.print_log(
                    "Begin recording match " + str(match_no) + " of " + str(length) + "...")
            match_history = add_match_data(match, match_history)
            current_length += 1
        else:
            text_colors.print_error("Skipping logged match...")
            if league_history:
                logged[0] = True
                return match_history
        match_no += 1
        if stop():
            break
    return match_history
