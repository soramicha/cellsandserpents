import sqlite3

def get_player_id_by_name(cur, name: str):
    """Get player id with name in currentGame"""
    cur.execute("SELECT id FROM currentGame WHERE name = ?", (name))
    result = cur.fetchone()
    return result[0] if result else None

def update_equipment(cur, con, player_id: int, new_equipment: str):
    """Update the equipment of a given player with a new string"""
    query = """
        UPDATE currentGame
        SET equipment = ?
        WHERE id = ?
    """
    cur.execute(query, (new_equipment, player_id))
    con.commit()

def update_stat(cur, con, player_id: int, field: str, delta: int):
    """Update the given field of the given player by delta (numerical only)"""
    allowed_fields = {"gold", "health", "attack", "defense", "speed", "charm", "intelligence", "magicPowers"}

    if field not in allowed_fields:
        raise ValueError(f"'{field}' is not a valid updatable stat.")
    
    query = f"""
        UPDATE currentGame
        SET {field} = {field} + ?
        WHERE id = ?
    """

    cur.execute(query, (delta, player_id))
    con.commit()

def print_player_stats(cur, player_id: int):
    """Print the given player's stats in currentGame"""
    cur.execute("SELECT * FROM currentGame WHERE id = ?", (player_id,))
    row = cur.fetchone()

    if not row:
        print("Player not found in currentGame.")
        return

    # get column names
    column_names = [desc[0] for desc in cur.description]

    print("--- Player Stats ---")
    for name, value in zip(column_names, row):
        print(f"{name.capitalize()}: {value}")
    print("---------------------\n")

def get_player_stats(cur, player_id: int):
    """Get player stats to use in AI prompt"""
    cur.execute("SELECT * FROM currentGame WHERE id = ?", (player_id,))
    row = cur.fetchone()

    if not row:
        print("Player not found in currentGame.")
        return
    
    return row


def test():
    # connect to the database
    con = sqlite3.connect("cellsandserpents.db")
    # so we can execute and fetch results from sql queries
    cur = con.cursor()

    try:
        cur.execute("CREATE TABLE currentGame (id, name, race, health, equipment, attack, defense, speed, charm, intelligence, magicPowers)")

        # print out template players to choose from
        cur.execute(f"""
            SELECT id, name FROM game
            """)
        data = cur.fetchall()

        for id, name in data:
            print(id, name)

        # pick a test player
        player = input(f"Please type in the id of player you want from the list: ")

        # check if player exists
        cur.execute(f"""
            SELECT * FROM game WHERE id == {player}
        """)
        data = cur.fetchall()

        if data is None:
            print("ID doesn't exist in the database. Please try again!")
        else:
            # save player data
            cur.execute("""
                INSERT INTO currentGame (id, name, race, health, equipment, attack, defense, speed, charm, intelligence, magicPowers)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data[0][0], data[0][1], data[0][2], data[0][3], data[0][4], data[0][5], data[0][6], data[0][7], data[0][8], data[0][9], data[0][10]))
            con.commit()

        player_id = data[0][0]

        print("\nOriginal:")
        print_player_stats(cur, player_id) 

        field = input(f"Please type in the field you want to change: ")
        delta = input(f"How much do you want to change it by? ")
        delta = int(delta)

        update_stat(cur, con, player_id, field, delta)

        print(f"Updated {field} by {delta}.\n")
        print_player_stats(cur, player_id)

        # when test finishes, drop the currentGame table
        cur.execute("DROP TABLE currentGame")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        cur.execute("DROP TABLE IF EXISTS currentGame")
        con.commit()
        con.close()

# test() # uncomment this to run test