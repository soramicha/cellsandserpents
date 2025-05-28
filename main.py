from google import genai
import os # to access env var
from dotenv import load_dotenv, find_dotenv
import sqlite3
# helper functions defined by ourselves
from update_stats import get_player_id_by_name, update_stat, print_player_stats

# load env file for the genai
_ = load_dotenv(find_dotenv())
key = os.environ.get('GEMINI_API_KEY')
client = genai.Client(api_key=key)

# connect to the database
con = sqlite3.connect("cellsandserpents.db")
# so we can execute and fetch results from sql queries
cur = con.cursor()

"""
storyData = {
    theme: ""


}


"""

storyData = {}

def GenAI(prompt):
    return client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt
    ).text

def kill_player(player_id):
    # fetch player from database
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

    #delete the player
    cur.execute("DELETE FROM currentGame WHERE id = ?", (player_id,))
    con.commit()
    return 0


    

def main():
    # welcome message
    cur.execute("DROP TABLE currentGame")
    player_count = input("""Hello there! Welcome to Cells and Serpents!\nHow many players will be joining today?\nType number here: """)

    data = {}

    # new database for the game
    cur.execute("CREATE TABLE currentGame (id, name, race, health, equipment, attack, defense, speed, charm, intelligence, magicPowers)")
    
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
                    INSERT INTO game (id, name, race, health, equipment, attack, defense, speed, charm, intelligence, magicPowers)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (id, name, race, health, equipment, attack, defense, speed, charm, intelligence, magicPower))
                con.commit()

                # add data into NEW database
                cur.execute("""
                    INSERT INTO currentGame (id, name, race, health, equipment, attack, defense, speed, charm, intelligence, magicPowers)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (i, name, race, health, equipment, attack, defense, speed, charm, intelligence, magicPower))
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
                        INSERT INTO currentGame (id, name, race, health, equipment, attack, defense, speed, charm, intelligence, magicPowers)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (data[0][0], data[0][1], data[0][2], data[0][3], data[0][4], data[0][5], data[0][6], data[0][7], data[0][8], data[0][9], data[0][10]))
                    con.commit()
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
    print("THIS ROUND:", data)

    theme_choice = input("Type a theme for the game: ")

    # store the theme info
    storyData["theme"] = theme_choice
    
    # give an opening to the game based on the theme choice players chose
    # allow players to pick choices in their journey
    print("\n" + GenAI(f"""
        the players in this data {str(data)} is a list of tuples. respectively, one tuple contains id, name, race, health level, equipments the player has, attack level, defense level, speed level, charm level, intelligence level, and magic power level.
        for the equipment parts, just understand those strings and make sure they are worded in a way it's understandable in human language. give a small opening paragraph for those players entering a surivival game based on the theme: {theme_choice}. when typing their names and stats if you choose to do so,
        don't add any quotation marks and make sure to capitalize the first letter of their names. make the opening funny too. for example, if a player is weak based on their stats, just say so and be direct and make fun of their levels and for people who are stronger, praise them A LOT""") + "\n")

    # add some game action stuff TODO
    cur.execute("SELECT id, name FROM currentGame WHERE health <= 0")
    dead_players = cur.fetchall()

    if dead_players:
        print("The following players have reached 0 health or below and died, let's see what happened.")
        for id, name in dead_players:
            print(name)
            kill_player(id)
        


    # note from angela:
    # to be able to update player + affected players, need the player id
    # would be best to have a variable storing the current player ID since most updates will happen to them

    # if you would like to update a player's stat that is NOT the current player:
    # use get_player_id_by_name(cur, player_name) 
    # ^ assuming all player names in currentGame are UNIQUE

    # can use the test() function in update_stats as an example of updating
    # can debug using the print_player_stats function

    # when game finishes, drop the currentGame table
    cur.execute("DROP TABLE currentGame")

main()