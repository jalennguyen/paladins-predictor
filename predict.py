from dotenv import load_dotenv
import os
from pyrez.api import PaladinsAPI
import pickle

# load in environment variables
load_dotenv()
DEV_ID = os.getenv("DEVELOPER_ID")
AUTH_KEY = os.getenv("AUTHENTICATION_KEY")

# create paladins object
paladins = PaladinsAPI(devId=DEV_ID, authKey=AUTH_KEY)


def get_champ(player_id, champ_id):
    # retrieve player's stats for each champion
    champions = paladins.getQueueStats(player_id, 486)

    # retrieve stats for current champion
    for champion in champions:
        if champion["ChampionId"] == champ_id:
            return champion

    # return blank stats if first time playing champion
    empty = {
            "Assists": 0,
            "Champion": None,
            "ChampionId": champ_id,
            "Deaths": 0,
            "Gold": 0,
            "Kills": 0,
            "LastPlayed": None,
            "Losses": 0,
            "Matches": 0,
            "Minutes": 0,
            "Queue": "",
            "Wins": 0,
            "player_id": str(player_id),
            "ret_msg": None
        }

    return empty


def raw_live_stats(team, i):
    stats = {
        "match_id": team[0]["Match"]
    }
    for player in team:
        # collect account stats
        stats[f"a_lvl{i}"] = player["Account_Level"]
        stats[f"tier{i}"] = player["Tier"]
        stats[f"wins{i}"] = player["tierWins"]
        stats[f"losses{i}"] = player["tierLosses"]
        stats[f"champ{i}"] = player["ChampionId"]

        # collect champion stats
        champ = get_champ(player["playerId"], player["ChampionId"])
        stats[f"assists{i}"] = champ["Assists"]
        stats[f"deaths{i}"] = champ["Deaths"]
        stats[f"kills{i}"] = champ["Kills"]
        stats[f"c_losses{i}"] = champ["Losses"]
        stats[f"c_matches{i}"] = champ["Matches"]
        stats[f"c_wins{i}"] = champ["Wins"]
        i += 1

    return stats


def live_stats(match):
    team1 = []
    team2 = []
    # split players into their respective teams
    for player in match:
        if player["taskForce"] == 1:
            team1.append(player)
        else:
            team2.append(player)

    # save match info
    match = {
        "match_id": match[0]['Match'],
        "winner": -1,
        "map": team1[0]["mapGame"],
        "region": team1[0]["playerRegion"],
        "date_time": -1
    }

    # get player stats for each team
    stats1 = raw_live_stats(team1, 1)
    stats2 = raw_live_stats(team2, 6)

    return [match, stats1, stats2]


def sums(team, i):
    sum_awr = 0
    sum_ckda = 0
    sum_cwr = 0

    # take sums of account w/r, champion w/r, and champion kda for the team
    for i in range(i, i + 5):
        matches_played = team[f"wins{i}"] + team[f"losses{i}"]
        if matches_played != 0:
            sum_awr += team[f"wins{i}"] / matches_played

        if team[f"deaths{i}"] == 0:
            sum_ckda += team[f"kills{i}"] + 0.5 * team[f"assists{i}"]
        else:
            sum_ckda += (team[f"kills{i}"] + 0.5 * team[f"assists{i}"]) / team[f"deaths{i}"]

        if team[f"c_matches{i}"] != 0:
            sum_cwr += team[f"c_wins{i}"] / team[f"c_matches{i}"]

    return sum_awr, sum_ckda, sum_cwr


def process_features(live_match):
    team1 = live_match[1]
    team2 = live_match[2]

    # calculate features for both teams
    sum_awr1, sum_ckda1, sum_cwr1 = sums(team1, 1)
    sum_awr2, sum_ckda2, sum_cwr2 = sums(team2, 6)

    # gather new features in a list for prediction
    features = [sum_awr1, sum_awr2,
                sum_ckda1, sum_ckda2,
                sum_cwr1, sum_cwr2]
    # round numbers
    features = [round(num, 4) for num in features]

    return features


def get_live_match(match_id):
    # retrieve info on live match
    match = paladins.getMatch(match_id, True)
    return match


def search_player(search):
    # attempt to find player from api
    results = paladins.getPlayerId(search)
    return results


def get_status(player_id):
    # return status for current player
    status = paladins.getPlayerStatus(player_id)
    return status


def player_info(match, player_id):
    # return account info for current player
    for player in match:
        if player_id == int(player['playerId']):
            return player


def predict_match(match):
    # error handling: disconnected player(s)
    if len(match) != 10:
        return -1

    # extract match stats from live match
    stats = live_stats(match)
    # process match features from stats for prediction
    features = process_features(stats)

    # load in classifier
    filename = "model.sav"
    model = pickle.load(open(filename, "rb"))

    # make match predictions
    proba = model.predict_proba([features])[0]
    return proba
