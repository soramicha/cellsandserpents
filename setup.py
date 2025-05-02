import sqlite3

# connect to the database
con = sqlite3.connect("cellsandserpents.db")
# so we can execute and fetch results from sql queries
cur = con.cursor()

# only execute once you actually have a table
# cur.execute("DROP TABLE game")

# create our table in the database
# currently commented out because it's been created, but if you haven't done it on your end, uncomment this to create your table
cur.execute("CREATE TABLE game(id, name, race, health, equipment, attack, defense, speed, charm, intelligence, magicPowers)")

# insert dummy data
cur.execute("""
    INSERT INTO game VALUES
        (0, 'Sophia', 'Fairy', 100, 'sword, shield', 80, 30, 40, 30, 40, 70),
        (1, 'Angela', 'Human', 100, '', 20, 50, 40, 90, 80, 50),
        (2, 'Bri', 'Hunter', 100, 'bow, arrows', 80, 30, 40, 30, 40, 70),
        (3, 'Amanda', 'Hunter', 100, 'bow, arrows', 80, 30, 40, 30, 40, 70)
""")
con.commit()

