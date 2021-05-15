from dotenv import load_dotenv
import os
from discord.ext.commands import Bot
import discord
from predict import search_player, get_status, get_live_match, player_info, predict_match

# load in environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")


# create an instance of Discord bot
bot = Bot(command_prefix="!")


@bot.event
async def on_ready():
    print(f'{bot.user} is now listening on Discord!')
    await bot.change_presence(activity=discord.Game('Paladins'))


@bot.command(name='predict', help='Calculates the probability of a player winning a ranked game')
async def predict(ctx, *, search):
    # search for player
    results = search_player(search)

    # no matches found
    if not results:
        await ctx.send(f'Player name {search} was not found.')
        return

    player = results[0]
    player_name = player['Name']
    player_id = player['player_id']

    if player['privacy_flag'] == "y":
        await ctx.send(f'{player_name} has Do Not Disturb enabled.')
        return

    # get player's status
    status = get_status(player_id)

    # player is in ranked match (able to predict)
    if status['status'] == 3 and status['match_queue_id'] == 486:
        match_id = status['Match']
        match = get_live_match(match_id)

        # get player's info
        info = player_info(match, player_id)
        champ_id = info['ChampionId']
        side = info['taskForce']

        # predict outcome of match
        split = predict_match(match)
        proba = split[side - 1] * 100
        proba = round(proba, 2)

        # change embed color based on win/loss prediction
        if proba >= 50:
            color = 0x00ff00
        else:
            color = 0xff0000

        # create discord embedded message
        embed = discord.Embed(title="Prediction:",
                              description=f"{player_name}'s team has a **{proba}%** chance of winning.",
                              color=color)

        icon_url_base = "https://raw.githubusercontent.com/jalennguyen/paladins-predictor/main/icons/"
        embed.set_author(name="PaladinsPredictor",
                         url="https://github.com/jalennguyen/paladins-predictor",
                         icon_url=f"{icon_url_base}2322.png")
        embed.set_footer(text=f'MatchId: {match_id}')
        embed.set_thumbnail(url=f"{icon_url_base}{champ_id}.png")

        await ctx.send(embed=embed)
        return

    # if not playing ranked, send player's status
    elif status['status'] == 0:
        await ctx.send(f'{player_name} is currently offline.')
        return

    elif status['status'] == 1:
        await ctx.send(f'{player_name} is currently in the lobby.')
        return

    else:
        await ctx.send(f'{player_name} is not currently in a ranked match.')
        return


@predict.error
async def predict_error(ctx, error):
    # handle error on !predict calls without arguments
    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.send("Please enter a player's name.")


if __name__ == "__main__":
    bot.run(TOKEN)
