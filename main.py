# from google import genai
import time
import google.generativeai as genai
import os # to access env var
import json
from dotenv import load_dotenv, find_dotenv
from collections import defaultdict
import sqlite3
import random
from datetime import datetime
# helper functions defined by ourselves
from update_stats import get_player_id_by_name, update_equipment, update_stat, print_player_stats, get_player_stats
import ast # to parse stat deltas
import re
# for terminal colors
from termcolor import colored
from pyfiglet import figlet_format, Figlet
from collections import defaultdict

# load env file for the genaix
_ = load_dotenv(find_dotenv())
key = os.environ.get('GEMINI_API_KEY')
# client = genai.Client(api_key=key)
genai.configure(api_key=key)

# connect to the database
con = sqlite3.connect("cellsandserpents.db")
# so we can execute and fetch results from sql queries
cur = con.cursor()

# to track story events
storyData = {
    "log": []
}

# to track individual player history
player_history = defaultdict(list)

def GenAI(prompt):
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
    return response.text

# generate a short summary of the outcome
def simplify_outcome(topic, full_text, player_name=None):
    prompt = f"""Summarize this story outcome in one or two short sentences.
    Focus on what happened to {player_name} if any (if it's blank, then just continue summarizing rest of everything), and mention any player names if involved because that's important, but skip any story fluff.
    If it's relevant to the topic {topic}, then make sure to mention any key info.
    Outcome: {full_text}"""
    summary = GenAI(prompt)
    return summary.strip()

# add a major story event to story log
def record_story_event(event_text):
    storyData["log"].append(event_text)

# track actions taken by individual player
def record_player_action(player_id, action_text):
    # store player_history based on ID
    player_history[player_id].append(action_text)

# save game history to a JSON file
def save_game_history():
    data = defaultdict(list)
    cur.execute("SELECT * FROM currentGame")
    d = cur.fetchall()
    for id, name, gold, health, equipment, attack, defense, speed, charm, intelligence in d:
        print(id, name, gold, health, equipment, attack, defense, speed, charm, intelligence)
        data[id] = [id, name, gold, health, equipment, attack, defense, speed, charm, intelligence]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"gameHistories/game_history{timestamp}.json", "w") as f:
        json.dump({
            "story": storyData,
            "playersHistory": player_history,
            "playersStats": data,
        }, f, indent=2)

def kill_player(player_id):
    # fetch player from data
    cur.execute("SELECT * FROM currentGame WHERE id = ?", (player_id,))
    player = cur.fetchone()

    if not player:
        print(f"No player found with id {player_id}")
        return
    
    # set up for story
    name = player[1]
    health = player[2]
    equipment = player[3]
    attack = player[4]
    defense = player[5]
    speed = player[6]
    charm = player[7]
    intelligence = player[8]

    story = GenAI(f"""A character named {name} has tragically died in the story: {storyData['log']}, here are their stats:
                  -Health: {health} -Equipment: {equipment} -Attack: {attack} -Defense: {defense} -Speed: {speed}
                    -Charm: {charm} -Intelligence: {intelligence}
                    Based on these stats and the storyline please write one short, over the top, dramatic, and very brutal paragraph (if necessary) on how they died.
                    Don't get off topic from the story!""")
    
    print("Death Report:")
    print(story)


    # delete the player

    cur.execute("DELETE FROM currentGame WHERE id = ?", (player_id,))
    con.commit()
    return 0

def coloredTitle():
    text = "Cells  &  Serpents"
    colors = ['red', 'green', 'yellow', 'blue', 'cyan', 'magenta', 'white']
    f = Figlet(font='small')

    for i in range(len(colors)):
        art = f.renderText(text)
        rainbow_art = ""
        for j, char in enumerate(art):
            if char == '\n':
                rainbow_art += char
            else:
                color = colors[(i + j) % len(colors)]
                rainbow_art += colored(char, color)
        # clear terminal
        print("\033c", end="")
        print(rainbow_art)

def main():
    coloredTitle()

    # drop currentGame table if it exists
    cur.execute("DROP TABLE IF EXISTS currentGame")

    # welcome message
    player_count = input("""Hello there! Welcome to Cells and Serpents!\nHow many players will be joining today?\nType number here: """)
    
    # store all player names involved in this round of game
    playerNames = []

    # new database for the game
    cur.execute("CREATE TABLE currentGame (id, name, health, gold, equipment, attack, defense, speed, charm, intelligence)")
    
    try:
        # convert input into integer
        player_count = int(player_count)

        if player_count == 0:
            print("0 players. I see...how sad. Game session ending...")
            return 0
        pickFromPreset = input(f"{player_count} players I see! Awesome, would you like to pick those characters from our preset character set? (Y/N) ")


        if pickFromPreset == "N" or pickFromPreset == "n":
            # retreive number of players for the game
            print("Please define each of your player information...\n")
        
            # fetch highest id we have right now
            cur.execute("SELECT MAX(id) FROM game")
            # fetch next index
            id = cur.fetchone()[0] + 1

            # store each player's data into the database
            for i in range(player_count):
                # skip if player_count was 0
                if player_count == 0:
                    break

                i = str(i)
                name = input("Type name of player " + i + ": ")
                equipment = input("Type a list of equipment(s) of player " + i + ": ")
                attack = input("Type attack level of player " + i + ": ")
                defense = input("Type defense level of player " + i + ": ")
                speed = input("Type speed level of player " + i + ": ")
                charm = input("Type charm level of player " + i + ": ")
                intelligence = input("Type intelligence level of player " + i + ": ")

                # type checking
                try:
                    # convert some inputs into integers
                    attack = int(attack)
                    defense = int(defense)
                    speed = int(speed)
                    charm = int(charm)
                    intelligence = int(intelligence)
                except ValueError:
                    print("What you typed in certain areas wasn't an integer when it was supposed to be. Ending session...")
                    return 0
                
                # store all data into the main database
                # default health = 100, default gold = 0
                cur.execute("""
                    INSERT INTO game (id, name, health, gold, equipment, attack, defense, speed, charm, intelligence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (id, name, 100, 0, equipment, attack, defense, speed, charm, intelligence))
                con.commit()

                # add data into NEW database
                cur.execute("""
                    INSERT INTO currentGame (id, name, health, gold, equipment, attack, defense, speed, charm, intelligence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (id, name, 100, 0, equipment, attack, defense, speed, charm, intelligence))
                con.commit()

                # save to playerNames
                playerNames.append((id, name))

                print("Player #" + i + " information added\n")
                # increment id for the next player
                id += 1

        else:
            print("Okay let's get straight into choosing from the preset characters then!\n")
        
            cur.execute(f"""
                SELECT id, name FROM game
                """)
            players = cur.fetchall()

            # allow users to pick players from the database
            for id, name in players:
                print(id, name)

            player_num = 0
            # keep asking what players to include until we finally reach the player_count
            while player_num != player_count:
                pInfo = input(f"Please type in the id of Player {player_num} you want from the list: ")
                
                # try to find it in the game table
                cur.execute(f"SELECT * FROM game WHERE id = {pInfo}")
                playerInfo = cur.fetchone()

                # if player isn't found...
                if playerInfo is None:
                    print("ID doesn't exist in the database. Please try again!")
                else:
                    # otherwise, increment the player_num
                    player_num += 1

                    # and save the player data into the currentGame table
                    cur.execute("""
                        INSERT INTO currentGame (id, name, health, gold, equipment, attack, defense, speed, charm, intelligence)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (playerInfo[0], playerInfo[1], playerInfo[2], playerInfo[3], playerInfo[4], playerInfo[5], playerInfo[6], playerInfo[7], playerInfo[8], playerInfo[9]))
                    con.commit()

                    # save to playerNames
                    playerNames.append((playerInfo[0], playerInfo[1]))

                    print("Saved Successfully")

    except ValueError:
        print("What you typed wasn't an integer. Ending session...")
        return 0
    

    # gets data of all players in this round of game
    cur.execute(f"SELECT * FROM currentGame")
    playersInGame = cur.fetchall()

    # prints out all players playing in this round
    print("Players registered for the game:", playersInGame)

    theme_choice = input("Type a theme for the game: ")

    # store the theme info
    storyData["theme"] = theme_choice
    
    # give an opening to the game based on the theme choice players chose
    # allow players to pick choices in their journey
    opening = GenAI(f"""
        The players in this data {str(playersInGame)} is a list of tuples. respectively, one tuple contains id, name, health level, equipments the player has, attack level, defense level, speed level, charm level, and intelligence level.
        for the equipment parts, just understand those strings and make sure they are worded in a way it's understandable in human language. give a small opening paragraph for those players entering a surivival game based on the theme: {theme_choice}. when typing their names,
        don't add any quotation marks and make sure to capitalize the first letter of their names. you may menion the stats but don't mention any stats numerically - just word them in english. for example, each stat is given 0 - 100 level, with 0 being bad and 100 being good.
        so just mention how good or bad each player is based on their stats. make the opening funny too. for example, if a player is weak based on their stats, just say so and be direct and make fun of their levels and for people who are stronger, praise them A LOT. also, don't state their id numbers.""")
    print("\n" + opening + "\n")

    # summarize opening and call record_story_event
    # store the opening
    record_story_event(simplify_outcome(theme_choice, opening))

    print("Your story...starts NOW!\n")

    # start players actions
    while True:
        # ask for each player's actions
        for pInfo in playersInGame:
            """ CREATE OUTCOME FOR EACH PLAYER """
            playerID = pInfo[0]
            playerName = pInfo[1]

            action = input(f"Enter an action {playerName} wants to do: ")

            # make sure successNum > success_rate in order to win
            success_rate = random.randint(0, 100)
            successNum = random.randint(0, 100)
            start_stats = get_player_stats(cur, pInfo[0])

            # produce outcome
            outcome = GenAI(f"""To be successful, success rate: {success_rate} must be < successNum: {successNum}. The amount of favoritism you give
                               to the user input {playerName} wishes to have depends on how well that inequality is. The bigger and farther away successNum
                               is from success rate, the better the outcome is, and worse if vice versa. Use these stats to help make the outcome: {start_stats},
                               which in order correspond to player id (ignore this), name, health, gold, equipment, attack, defense, speed, charm, and intelligence. The action {playerName} wishes to do is: {action}. 
                               Give a few sentences-long outcome based on this (write it in a casual personified way), and make sure to state the original 
                               wish of {playerName} in a creative manner. don't include anything about success rates! Give it appropriately based on the story 
                               history here - don't go off topic: {storyData['log']}. The player history, if any of {playerName} is: 
                               {player_history[playerID]}. Also, if there are any other players involved in the list {playerNames} besides the current {playerName}, then
                               also consider the success rate and how well the action could be executed based on other players' stats. Search their stats
                               here: {playersInGame} and match data based on the names. Make sure to give only one clear outcome that reads like a cohesive paragraph.""")

            # summarize the outcome - player history
            summary = simplify_outcome(theme_choice, outcome, playerName)

            # record story event
            record_story_event(summary)

            """ CHECK FOR ANY AFFECTED PLAYERS AND UPDATE EVERYONE'S STATS AS NECESSARY """
            # TODO UPDATING STATS IS IFFY
            # first check any affected players from current action
            for id, pName in playerNames:
                checkAffectedPlayers = GenAI(f"check if {outcome} involves {pName}. return a single letter T if so, otherwise F")
                # if affected
                if checkAffectedPlayers == "T\n":
                    # record the player's summary
                    record_player_action(id, summary)

                    currentp_stats = get_player_stats(cur, id)
                    print("current stats", currentp_stats)
                    player_equipment = currentp_stats[4]

                    # get updated json stats of current player
                    update_stats = GenAI(f"""Based on this paragraph {outcome}, return a list of estimated numerical stat deltas from -50 to 50
                                          for {pName} in the category of "health". 
                                          For the category of "gold", the delta is a reasonable amount gained/lost based on the paragraph.
                                          If there is no effect, just assign the category a score of 0.
                                          For the category "equipment", set it as a string that describes what equipment they have after event, 
                                          based off of their previous equipment {player_equipment}. Make sure to keep any previous equipment if it's not used or broken, etc. If there's an empty string for player equipment,
                                          that just means the player had no equipment before, so don't worry about keeping any previous equipment.
                                          Remember is someone is stealing something from another player the player who stole it should gain it and the
                                          player that was stolen from should lose it.
                                          Please return in the format of a proper JSON list such as 
                                          ["gold": 0, "equipment": "old shield", "health": -10], replacing the square brackets with curly braces.
                                         Please don't give any explanation after - just the formatted JSON.""")
                    
                    print(f"For player {pName}:")
                    print(update_stats)

                    # attempt to parse and apply updates
                    try:
                        # Remove triple backticks and markdown syntax if present
                        cleaned_update_stats = re.sub(r"```.*?\n|```", "", update_stats).strip()
                        stat_changes = ast.literal_eval(cleaned_update_stats)
                        print(stat_changes, "are the stat changes for", pName)
                        for stat, delta in stat_changes.items():
                            if stat == "equipment" and stat_changes["equipment"] != 0:
                                update_equipment(cur, con, id, stat_changes["equipment"])
                            else:
                                print("updating", stat, "by", delta)
                                update_stat(cur, con, id, stat, delta)
                                cur.execute("SELECT * FROM currentGame WHERE id == ?", (id,))
                                ifn = cur.fetchone()
                                print("updated", stat, "By", delta, "for", pName, ifn)
                    except Exception as e:
                        print(f"Error updating stats for {pName}: {e}")

            # prints outcome
            print(outcome)

            """ CHECK FOR DEATHS """
            # check if the player dies
            cur.execute("SELECT * FROM currentGame WHERE id = ?", (playerID,))
            row = cur.fetchone()
            print("health of", playerName, row[3])
            if row[3] <= 0:
                print(f"{playerName} has reached 0 health or below and died, let's see what happened.")
                kill_player(playerID)
                
                # remove from playerNames as well
                playerNames.remove((playerID, playerName))

                # update - get of all players in this round of game
                cur.execute(f"SELECT * FROM currentGame")
                playersInGame = cur.fetchall()

        # if there are still more remaining players in the game, make sure to continue
        if playersInGame != []:
            uInput = input("Type 'end' to save the story and end the game: ")
            if uInput == "end":
                break
        else:
            # otherwise, end the story
            break

    print("Saving game history...\nThank you for playing Cells & Serpents!")
    
    # save game history
    save_game_history()

    # when game finishes, drop the currentGame table
    cur.execute("DROP TABLE IF EXISTS currentGame")

main()