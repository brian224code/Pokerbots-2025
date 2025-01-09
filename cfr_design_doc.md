## CFR Bot Design Doc

# CFR Algorithm
![Pseudocode](image.png)

# Hand Buckets

Use hierarchical buckets
- using either eval 7 or win prob, or some other metric of hand strength 
- first bool is for if hit bounty or not, and rest are divided on hand strength

preflop = ([0, 1], [1,10])

flop = ([0, 1], [1, 10], [1, 10])

turn = ([0, 1], [1, 10], [1, 10], [1, 10])

river = ([0, 1], [1, 10], [1, 10], [1, 10])

# Action Buckets

- Call
- Fold
- Check
- Raise (min raise, max raise/all in, 1/3 pot, 1/2 pot, full pot, 1.5 pot, 2 pot)

# Implementation Details

- persist weights as csv and read them into a matrix at runtime

# Other Ideas
- base bot weights that are loaded in each game and have the bot do "fine tunes" within each game (1000 rounds) or even for each bot

# TODO
- what language
- how to calc hand strength 
