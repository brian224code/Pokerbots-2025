import eval7
import matplotlib.pyplot as plt
import numpy as np

# Read in log file and prompt user for player identity
log_file_path = "game_log_analyze.txt"

# Read in text file
with open(log_file_path, "r") as file:
    log_content = file.readlines()

# Get player is A or player is B
player_identity = input("Enter the player's identity: ")
player_identity = player_identity.upper()

if player_identity != "A" and player_identity != "B":
    raise NameError()

# Extract the wins/losses of your player in a round-by-round basis
stack_tracker = []
for line in log_content:
    # Check for the player's actions in each round
    if player_identity in line:
        if "awarded" in line:
            awarded_amount = int(line.split("awarded")[1])
            stack_tracker.append(awarded_amount)

cumulative_sum = np.cumsum(stack_tracker)
plt.plot(cumulative_sum, color='b')
plt.title('Cumulative Sum Over Time')
plt.xlabel('Time')
plt.ylabel('Cumulative Sum')
plt.grid(True)
plt.show()

log_content = "".join(log_content)
rounds = log_content.split('Round #')
rounds = rounds[1:]

for i, val in enumerate(stack_tracker):
    if val <= -100:
        print(rounds[i])

