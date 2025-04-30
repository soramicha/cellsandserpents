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
    # retreive number of players for the game
    print(player_count, "players I see! Awesome, please define each of your player information...\n")

    # name, race, health, equipment, attack, defense, speed, personality (charm, intelligence, magic power)
    # TODO
    for row in cur.execute("SELECT * FROM game"):
        print(row)
main()