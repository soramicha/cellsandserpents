# from google import genai
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

# load env file for the genai
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
player_history = {}

"""def GenAI(prompt):
    return client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt
    ).text"""

def GenAI(prompt):
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
    return response.text

# generate a short summary of the outcome
def simplify_outcome(full_text, player_name):
    prompt = f"""Summarize this story outcome in one short sentence.
    Focus on what happened to {player_name}, and mention any player names if involved because that's important, but skip any story fluff.
    Outcome: {full_text}"""
    summary = GenAI(prompt)
    return summary.strip()

# add a major story event to story log
def record_story_event(event_text):
    storyData["log"].append(event_text)

# track actions taken by individual player
def record_player_action(player_id, action_text):
    if player_id not in player_history:
        player_history[player_id] = []
    player_history[player_id].append(action_text)

# save game history to a JSON file
def save_game_history():
    data = defaultdict(list)
    cur.execute("SELECT * FROM currentGame")
    d = cur.fetchall()
    for id, name, race, gold, health, equipment, attack, defense, speed, charm, intelligence, magicPowers in d:
        print(id, name, race, gold, health, equipment, attack, defense, speed, charm, intelligence, magicPowers)
        data[id] = [id, name, race, gold, health, equipment, attack, defense, speed, charm, intelligence, magicPowers]

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
    race = player[2]
    health = player[3]
    equipment = player[4]
    attack = player[5]
    defense = player[6]
    speed = player[7]
    charm = player[8]
    intelligence = player[9]
    magic_power = player[10]

    story = GenAI(f"""A character named {name} ({race}) has tragically died in the cells and serpants, here are their stats:
                  -Health: {health} -Equipment: {equipment} -Attack: {attack} -Defense: {defense} -Speed: {speed}
                    -Charm: {charm} -Intelligence: {intelligence} -Magic Power: {magic_power}
                    Based on these stats please write one short, over the top, dramatic, and very brutal paragraph on how they died""")
    
    print("Death Report:")
    print(story)


    # delete the player

    cur.execute("DELETE FROM currentGame WHERE id = ?", (player_id,))
    con.commit()
    return 0

def main():
    # drop currentGame table if it exists
    cur.execute("DROP TABLE IF EXISTS currentGame")

    # welcome message
    player_count = input("""Hello there! Welcome to Cells and Serpents!\nHow many players will be joining today?\nType number here: """)
    playerNames = []

    data = {}

    # new database for the game
    cur.execute("CREATE TABLE currentGame (id, name, race, health, gold, equipment, attack, defense, speed, charm, intelligence, magicPowers)")
    
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
        
            # fetch next index
            cur.execute("SELECT COUNT(*) FROM game")
            id = cur.fetchone()[0]

            # store each player's data into the database
            for i in range(player_count):
                # skip if player_count was 0
                if player_count == 0:
                    break

                i = str(i)
                name = input("Type name of player " + i + ": ")
                race = input("Type race of player " + i + ": ")
                health = input("Type health of player " + i + ": ")
                equipment = input("Type a list of equipment(s) of player " + i + ": ")
                attack = input("Type attack level of player " + i + ": ")
                defense = input("Type defense level of player " + i + ": ")
                speed = input("Type speed level of player " + i + ": ")
                # personality
                charm = input("Type charm level of player " + i + ": ")
                intelligence = input("Type intelligence level of player " + i + ": ")
                magicPower = input("Type magic power level of player " + i + ": ")

                # type checking
                try:
                    # convert some inputs into integers
                    health = int(health)
                    attack = int(attack)
                    defense = int(defense)
                    speed = int(speed)
                    charm = int(charm)
                    intelligence = int(intelligence)
                    magicPower = int(magicPower)
                except ValueError:
                    print("What you typed in certain areas wasn't an integer when it was supposed to be. Ending session...")
                    return 0
                
                # store all data into the main database
                cur.execute("""
                    INSERT INTO game (id, name, race, health, gold, equipment, attack, defense, speed, charm, intelligence, magicPowers)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (id, name, race, health, 0, equipment, attack, defense, speed, charm, intelligence, magicPower))
                con.commit()

                # save to playerNames
                playerNames.append((id, name))

                # initialize player_history for the player
                player_history[id] = []

                # add data into NEW database
                cur.execute("""
                    INSERT INTO currentGame (id, name, race, health, gold, equipment, attack, defense, speed, charm, intelligence, magicPowers)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (i, name, race, health, 0, equipment, attack, defense, speed, charm, intelligence, magicPower))
                con.commit()

                print("Player #" + i + " information added\n")
                # increment id
                id += 1

        else:
            print("Okay let's get straight into choosing from the preset characters then!\n")

            cur.execute(f"""
                SELECT id, name FROM game
                """)
            data = cur.fetchall()
            # allow users to pick players from the database TODO
            for id, name in data:
                print(id, name)

            i = 0
            while i != player_count:
                player = input(f"Please type in the id of Player {i} you want from the list: ")

                # check if player exists
                cur.execute(f"""
                    SELECT * FROM game WHERE id == {player}
                """)
                data = cur.fetchall()

                if data is None:
                    print("ID doesn't exist in the database. Please try again!")
                else:
                    i += 1

                    # save player data
                    cur.execute("""
                        INSERT INTO currentGame (id, name, race, health, gold, equipment, attack, defense, speed, charm, intelligence, magicPowers)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (data[0][0], data[0][1], data[0][2], data[0][3], 0, data[0][4], data[0][5], data[0][6], data[0][7], data[0][8], data[0][9], data[0][10]))
                    con.commit()

                    # initialize player_history for the player
                    player_history[data[0][0]] = []

                    # save to playerNames
                    playerNames.append((data[0][0], data[0][1]))

                    print("Saved Successfully")

    except ValueError:
        print("What you typed wasn't an integer. Ending session...")
        return 0
    
    # gets data of all players in this round of game
    cur.execute(f"""
        SELECT * FROM currentGame
        """)
    data = cur.fetchall()

    # prints out all players playing in this round
    print("Players registered for the game:", data)

    theme_choice = input("Type a theme for the game: ")

    # store the theme info
    storyData["theme"] = theme_choice
    
    # give an opening to the game based on the theme choice players chose
    # allow players to pick choices in their journey
    opening = GenAI(f"""
        The players in this data {str(data)} is a list of tuples. respectively, one tuple contains id, name, race, health level, equipments the player has, attack level, defense level, speed level, charm level, intelligence level, and magic power level.
        for the equipment parts, just understand those strings and make sure they are worded in a way it's understandable in human language. give a small opening paragraph for those players entering a surivival game based on the theme: {theme_choice}. when typing their names and stats if you choose to do so,
        don't add any quotation marks and make sure to capitalize the first letter of their names. make the opening funny too. for example, if a player is weak based on their stats, just say so and be direct and make fun of their levels and for people who are stronger, praise them A LOT. also, don't state their id numbers.""")
    print("\n" + opening + "\n")

    # store the opening
    record_story_event(opening)

    print("Your story...starts NOW!\n")
    # start players actions
    while True:
        # ask for each player's actions
        for player in data:
            action = input(f"Enter what action {player[1]} wants to do: ")

            # make sure successNum > success_rate in order to win
            success_rate = random.randint(0, 100)
            successNum = random.randint(0, 100)
            start_stats = get_player_stats(cur, player[0])

            # print(f"start stats: {start_stats}")

            # produce outcome
            outcome = GenAI(f"""To be successful, success rate: {success_rate} must be < successNum: {successNum}. The amount of favoritism you give
                               to the user input {player[1]} wishes to have depends on how well that inequality is. The bigger and farther away successNum
                               is from success rate, the better the outcome is, and worse if vice versa. Use these stats to help make the outcome: {start_stats},
                               which in order correspond to player id (ignore this), name, race, health, gold, equipment, attack, defense, speed, charm, intelligence,
                               and magic powers. The action {player[1]} wishes to do is: {action}. 
                               Give a few sentences-long outcome based on this (write it in a casual personified way), and make sure to state the original 
                               wish of {player[1]} in a creative manner. don't include anything about success rates! Give it appropriately based on the story 
                               history here - don't go off topic: {storyData['log']}. The player history, if any of {player[1]} is: 
                               {player_history[player[0]]}. Also, if there are any other players involved in the list {playerNames} besides the current {player[1]}, then
                               also consider the success rate and how well the action could be executed based on that other player's stats. Search their stats
                               here: {cur.fetchall()} and match data based on the names. Make sure to give only one clear outcome that reads like a cohesive paragraph.""")

            # summarize the outcome - player history
            summary = simplify_outcome(outcome, player[1])

            # save in player history
            for id, p in playerNames:
                checkAffectedPlayers = GenAI(f"""check if {outcome} involves {p}. return a single letter T if so, otherwise F""")
                if checkAffectedPlayers == "T\n":
                    record_player_action(id, {
                        "summary": summary
                    })
                    currentp_stats = get_player_stats(cur, id)
                    player_equipment = currentp_stats[5]

                    update_stats = GenAI(f"""Based on this paragraph {outcome}, return a list of estimated numerical stat deltas from -10 to 10
                                          for {p} in the categories of "health", "attack", "defense", "speed", "charm", "intelligence", "magicPowers". 
                                          For the category of "gold", the delta is a reasonable amount gained/lost based on the paragraph.
                                          If there is no effect, just assign the category a score of 0.
                                          For the category "equipment", set it as a string that describes what equipment they have after event, 
                                          based off of their previous equipment {player_equipment}. Please return in the format of a proper JSON list such as 
                                          ["gold": 0, "equipment": "old shield", "health": -10, "attack": 1, ...], replacing the square brackets with curly braces.
                                         Please don't give any explanation after - just the formatted JSON.""")
                    
                    print(f"for player {p}")
                    print(update_stats)

                    # attempt to parse and apply updates
                    try:
                        # Remove triple backticks and markdown syntax if present
                        cleaned_update_stats = re.sub(r"```.*?\n|```", "", update_stats).strip()
                        stat_changes = ast.literal_eval(cleaned_update_stats)
                        # print(f"stat changes list: {stat_changes}")
                        
                        for stat, delta in stat_changes.items():
                            if stat == "equipment" and stat_changes["equipment"] != 0:
                                update_equipment(cur, con, id, stat_changes["equipment"])
                            else:
                                update_stat(cur, con, id, stat, delta)
                    except Exception as e:
                        print(f"Error updating stats for {p}: {e}")

            # prints outcome
            print(outcome)

        uInput = input("Type 'end' to save the story and end the game: ")
        if uInput == "end":
            break

    # add some game action stuff TODO
    cur.execute("SELECT id, name FROM currentGame WHERE health <= 0")
    dead_players = cur.fetchall()

    if dead_players:
        print("The following players have reached 0 health or below and died, let's see what happened.")
        for id, name in dead_players:
            print(name)
            kill_player(id)
        

    # save game history
    save_game_history()

    # when game finishes, drop the currentGame table
    cur.execute("DROP TABLE IF EXISTS currentGame")

main()