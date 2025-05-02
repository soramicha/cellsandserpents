from google import genai
import os # to access env var
from dotenv import load_dotenv, find_dotenv
import sqlite3

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

def main():
    # welcome message
    player_count = input("""Hello there! Welcome to Cells and Serpents!\nHow many players will be joining today?\nType number here: """)

    data = {}
    try:
        # convert input into integer
        player_count = int(player_count)

        if player_count != 0:
            # retreive number of players for the game
            print(player_count, "players I see! Awesome, please define each of your player information...\n")
        
            # fetch next index
            cur.execute("SELECT COUNT(*) FROM game")
            start_id = id = cur.fetchone()[0]

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
                
                # store all data into the database
                cur.execute("""
                    INSERT INTO game (id, name, race, health, equipment, attack, defense, speed, charm, intelligence, magicPowers)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (id, name, race, health, equipment, attack, defense, speed, charm, intelligence, magicPower))
                con.commit()
                print("Player #" + i + " information added\n")
                # increment id
                id += 1

            # gets data of all players in this round of game
            cur.execute(f"""
                SELECT * FROM game WHERE id >= {start_id}
                """)
            data = cur.fetchall()
            # prints out all players playing in this round
            print("THIS ROUND:", data)

        else:
            print("Okay let's get straight into choosing from the preset characters then!\n")
            # allow users to pick players from the database TODO

    except ValueError:
        print("What you typed wasn't an integer. Ending session...")
        return 0

    theme_choice = input("Type a theme for the game: ")

    # store the theme info
    storyData["theme"] = theme_choice
    
    # give an opening to the game based on the theme choice players chose
    # allow players to pick choices in their journey
    print(GenAI(f"""\n
        the players in this data {str(data)}
        where index 1 is their name. give a small opening paragraph for those players entering a surivival game based on the theme: {theme_choice}. when typing their names and stats if you choose to do so,
        don't add any quotation marks and make sure to capitalize the first letter of their names"""))

main()