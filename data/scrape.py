from dotenv import load_dotenv
import os
from pyrez.api import PaladinsAPI
import pandas as pd

load_dotenv()
DEV_ID = os.getenv("DEVELOPER_ID")
AUTH_KEY = os.getenv("AUTHENTICATION_KEY")

# create paladins object
paladins = PaladinsAPI(devId=DEV_ID, authKey=AUTH_KEY)


def team_stats(team, i):
    stats = {
        "match_id": team[0]["Match"]
    }
    for player in team:
        # get account stats
        stats[f"a_lvl{i}"] = player["Account_Level"]
        if player["League_Tier"] == 0:
            stats[f"tier{i}"] = None
        else:
            stats[f"tier{i}"] = player["League_Tier"]
        stats[f"wins{i}"] = player["League_Wins"]
        stats[f"losses{i}"] = player["League_Losses"]
        stats[f"champ{i}"] = player["ChampionId"]

        # get champion stats
        champ = get_champ(player["playerId"], player["ChampionId"])
        stats[f"assists{i}"] = champ["Assists"]
        stats[f"deaths{i}"] = champ["Deaths"]
        stats[f"kills{i}"] = champ["Kills"]
        stats[f"c_losses{i}"] = champ["Losses"]
        stats[f"c_matches{i}"] = champ["Matches"]
        stats[f"c_wins{i}"] = champ["Wins"]
        i += 1

    return stats


def match_stats(match_id):
    # retrieve all players in current match
    match = paladins.getMatch(match_id)

    if not match:
        print("No matches could be found for inputted date.")
        quit()

    # split players into their respective teams
    team1 = []
    team2 = []
    for player in match:
        if player["TaskForce"] == 1:
            team1.append(player)
        else:
            team2.append(player)

    # create dict for match info
    match_info = {
        "match_id": team1[0]["Match"],
        "winner": team1[0]["Winning_TaskForce"] - 1,
        "map": team1[0]["Map_Game"],
        "region": team1[0]["Region"],
        "date_time": team1[0]["Entry_Datetime"]
    }

    # aggregate stats for each team
    stats1 = team_stats(team1, 1)
    stats2 = team_stats(team2, 6)

    return match_info, stats1, stats2


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
            "ChampionId": None,
            "Deaths": 0,
            "Gold": 0,
            "Kills": 0,
            "LastPlayed": None,
            "Losses": 0,
            "Matches": 0,
            "Minutes": 0,
            "Queue": "",
            "Wins": 0,
            "player_id": None,
            "ret_msg": None
        }

    return empty


def get_ids():
    while True:
        date = input("Enter desired date as YYYYMMDD: ")
        hour = int(input("Enter hour 0 - 23: "))
        limit = int(input("Enter maximum # of matches to be returned: "))

        # retrieve batch of ids from api
        match_ids = paladins.getMatchIds(486, date, hour)
        if not match_ids:
            print("No match ids found!")
        else:
            break

    # limit number of match ids returned
    if len(match_ids) > limit:
        match_ids = match_ids[:limit]

    # format returned match ids
    for i in range(len(match_ids)):
        match_ids[i] = int(str(match_ids[i])[9:-1])

    return match_ids


def scrape(match_ids):
    matches = []
    team1 = []
    team2 = []

    # store data from each match in lists
    for id in match_ids:
        match, stats1, stats2 = match_stats(id)
        matches.append(match)
        team1.append(stats1)
        team2.append(stats2)

    # transform lists into dataframes
    matches = pd.DataFrame(matches)
    team1 = pd.DataFrame(team1)
    team2 = pd.DataFrame(team2)

    # assigning column orders to dataframes
    col1 = ['match_id',
            'a_lvl1', 'a_lvl2', 'a_lvl3', 'a_lvl4', 'a_lvl5',
            'tier1', 'tier2', 'tier3', 'tier4', 'tier5',
            'wins1', 'wins2', 'wins3', 'wins4', 'wins5',
            'losses1', 'losses2', 'losses3', 'losses4', 'losses5',
            'champ1', 'champ2', 'champ3', 'champ4', 'champ5',
            'assists1', 'assists2', 'assists3', 'assists4', 'assists5',
            'deaths1', 'deaths2', 'deaths3', 'deaths4', 'deaths5',
            'kills1', 'kills2', 'kills3', 'kills4', 'kills5',
            'c_losses1', 'c_losses2', 'c_losses3', 'c_losses4', 'c_losses5',
            'c_matches1', 'c_matches2', 'c_matches3', 'c_matches4', 'c_matches5',
            'c_wins1', 'c_wins2', 'c_wins3', 'c_wins4', 'c_wins5']
    col2 = ['match_id',
            'a_lvl6', 'a_lvl7', 'a_lvl8', 'a_lvl9', 'a_lvl10',
            'tier6', 'tier7', 'tier8', 'tier9', 'tier10',
            'wins6', 'wins7', 'wins8', 'wins9', 'wins10',
            'losses6', 'losses7', 'losses8', 'losses9', 'losses10',
            'champ6', 'champ7', 'champ8', 'champ9', 'champ10',
            'assists6', 'assists7', 'assists8', 'assists9', 'assists10',
            'deaths6', 'deaths7', 'deaths8', 'deaths9', 'deaths10',
            'kills6', 'kills7', 'kills8', 'kills9', 'kills10',
            'c_losses6', 'c_losses7', 'c_losses8', 'c_losses9', 'c_losses10',
            'c_matches6', 'c_matches7', 'c_matches8', 'c_matches9', 'c_matches10',
            'c_wins6', 'c_wins7', 'c_wins8', 'c_wins9', 'c_wins10']
    team1 = team1[col1]
    team2 = team2[col2]

    # export data to csv
    matches.to_csv("match.csv", mode="a", index=False, header=False)
    team1.to_csv("team1.csv", mode="a", index=False, header=False)
    team2.to_csv("team2.csv", mode="a", index=False, header=False)
    print("Exported", len(match_ids), "matches successfully!")


if __name__ == "__main__":
    match_ids = get_ids()
    scrape(match_ids)
