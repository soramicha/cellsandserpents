Changes Sophia Made to the Game:

- added Cells and Serpents styling
- fixed error of adding new characters (new characters are added with the id being the highest id in the game table + 1 so no overlapping of ids will ever occur if we ever delete any characters from the table games)
- removed the 'race' and 'magicPower' columns in all games because it's unnecessary towards the story game
- assigned all starting health default to 100
- now the game ends when there aren't alive players left
- only allow stat updates of health and gold and equipment!

# CURRENT PROBLEM: updating stats for players affected isn't working well and so is the equipment update

Improvements WE COULD MAKE:
- load game history back into the game
- register new characters while also picking from the preset
- find a new way to register equipment