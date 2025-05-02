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

def GenAI():
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents="tell me about a fairy dying in a small paragraph"
    )

    print(response.text)

def main():
    # welcome message
    player_count = input("""Hello there! Welcome to Cells and Serpents!\nHow many players will be joining today?\nType number here: """)

    try:
        # convert input into integer
        player_count = int(player_count)
        # retreive number of players for the game
        print(player_count, "players I see! Awesome, please define each of your player information...\n")

    except ValueError:
        print("What you typed wasn't an integer. Ending session...")

    # store each player's data into SQLite
    for i in range(player_count):
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

        # store all data into the database
        cur.execute("""
            INSERT INTO game (name, race, health, equipment, attack, defense, speed, charm, intelligence, magicPowers)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, race, health, equipment, attack, defense, speed, charm, intelligence, magicPower))
        con.commit()
        print("Player #" + i + " information added\n")

    # name, health, attack, defense, speed, personality (charm, intelligence, magic power)
    # TODO
    for row in cur.execute("SELECT * FROM game"):
        print(row)
main()