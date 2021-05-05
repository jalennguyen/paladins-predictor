import pickle
from pyrez.api import PaladinsAPI
from scrape import get_champ

# authorize with paladins api
paladins = PaladinsAPI(devId=0000, authKey="0000")


def live_team_stats(team, i):
    stats = {
        "match_id": team[0]["Match"]
    }
    for player in team:
        stats[f"a_lvl{i}"] = player["Account_Level"]
        stats[f"tier{i}"] = player["Tier"]
        stats[f"wins{i}"] = player["tierWins"]
        stats[f"losses{i}"] = player["tierLosses"]
        stats[f"champ{i}"] = player["ChampionId"]

        champ = get_champ(player["playerId"], player["ChampionId"])
        stats[f"assists{i}"] = champ["Assists"]
        stats[f"deaths{i}"] = champ["Deaths"]
        stats[f"kills{i}"] = champ["Kills"]
        stats[f"c_losses{i}"] = champ["Losses"]
        stats[f"c_matches{i}"] = champ["Matches"]
        stats[f"c_wins{i}"] = champ["Wins"]
        i += 1

    return stats


def live_stats(match_id, player_id):
    # retrieve info on live match
    match = paladins.getMatch(match_id, True)

    side = 0
    team1 = []
    team2 = []
    # split players into their respective teams
    for player in match:
        if player["taskForce"] == 1:
            team1.append(player)
        else:
            if player["playerId"] == str(player_id):
                side = 1
            team2.append(player)

    # save match info
    match = {
        "match_id": match_id,
        "winner": -1,
        "map": team1[0]["mapGame"],
        "region": team1[0]["playerRegion"],
        "date_time": -1
    }

    # get player stats for each team
    stats1 = live_team_stats(team1, 1)
    stats2 = live_team_stats(team2, 6)

    return [match, stats1, stats2], side


def summed_wr(live_match):
    # process raw stats for team1
    team1 = live_match[1]
    sum_awr1 = 0
    sum_ckda1 = 0
    sum_cwr1 = 0
    for i in range(1, 6):
        matches_played = team1[f"wins{i}"] + team1[f"losses{i}"]
        if matches_played != 0:
            sum_awr1 += team1[f"wins{i}"] / matches_played

        if team1[f"deaths{i}"] == 0:
            sum_ckda1 += team1[f"kills{i}"] + 0.5 * team1[f"assists{i}"]
        else:
            sum_ckda1 += (team1[f"kills{i}"] + 0.5 * team1[f"assists{i}"]) / team1[f"deaths{i}"]

        if team1[f"c_matches{i}"] != 0:
            sum_cwr1 += team1[f"c_wins{i}"] / team1[f"c_matches{i}"]

    # process raw stats for team2
    team2 = live_match[2]
    sum_awr2 = 0
    sum_ckda2 = 0
    sum_cwr2 = 0
    for i in range(6, 11):
        matches_played = team2[f"wins{i}"] + team2[f"losses{i}"]
        if matches_played != 0:
            sum_awr2 += team2[f"wins{i}"] / matches_played

        if team2[f"deaths{i}"] == 0:
            sum_ckda2 += team2[f"kills{i}"] + 0.5 * team2[f"assists{i}"]
        else:
            sum_ckda2 += (team2[f"kills{i}"] + 0.5 * team2[f"assists{i}"]) / team2[f"deaths{i}"]

        if team2[f"c_matches{i}"] != 0:
            sum_cwr2 += team2[f"c_wins{i}"] / team2[f"c_matches{i}"]

    # gather new features in a list for prediction
    sums = [sum_awr1, sum_awr2, sum_ckda1, sum_ckda2, sum_cwr1, sum_cwr2]
    sums = [round(num, 4) for num in sums]

    return sums


def predict(player):
    stats, side = live_stats(player["match"], player["id"])
    # process match features for prediction
    processed = summed_wr(stats)

    # load in classifier
    filename = "model.sav"
    model = pickle.load(open(filename, "rb"))

    # make match predictions
    proba = model.predict_proba([processed])
    print("Prediction:", player["name"], "'s team has a", round(proba[0][side] * 100, 2), "chance of winning.")


def find_player():
    player = {}
    while True:
        search = input("Enter player name (or -q to quit): ")

        # quit search
        if search == "-q":
            print("See ya later!")
            quit()

        # retrieve player from api
        results = paladins.getPlayerId(search)

        if not results:
            print("Player ", search, " could not be found.")

        elif len(results) == 1:
            print("Player found!")
            player["id"] = results[0]["player_id"]
            player["name"] = results[0]["Name"]
            break

        else:
            print(results)
            select = int(input("Which player? "))
            while select < 1 or select > len(results):
                select = int(input("Choose a number between 1 and ", len(results)))
            player["id"] = results[select - 1]["player_id"]
            player["name"] = results[select - 1]["Name"]
            break

    # get player status for current search
    status = paladins.getPlayerStatus(player["id"])
    player["match"] = status["Match"]

    if status["status"] == 3 and status["match_queue_id"] == 486:
        return player

    elif status["status"] == 0:
        print(player["name"], "is offline.")
        return find_player()

    elif status["status"] == 1:
        print(player["name"], "is in the lobby.")
        return find_player()

    else:
        print(player["name"], "is not in a ranked match.")
        return find_player()


if __name__ == "__main__":
    player = find_player()
    predict(player)
