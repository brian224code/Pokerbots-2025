import pandas as pd
import csv
#from python_skeleton.history import RAISES, NUM_ACTIONS

NUM_ACTIONS = 7

def save_to_csv(filename, data):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        header = ['information set'] + [f'action {i}' for i in range(NUM_ACTIONS)]
        writer.writerow(header)
        for info_set, values in data.items():
            writer.writerow([info_set] + list(values))
    print(f'Saved data to {filename}.')

def load_from_csv(filename):
    df = pd.read_csv(filename)

    table = {
        str(row['information set']) : [float(row[f'action {i}']) for i in range(NUM_ACTIONS)]
        for _, row in df.iterrows()
    }

    return table

FOLD = 0
CALL = 1
CHECK = 2
MAX_RAISE = 3
RAISE_20 = 4
RAISE_40 = 5
RAISE_80 = 6
LARGE_REGRET = 9999999

# Read in log file and prompt user for player identity
cumulative_regret_file_path = input("Enter the file path: ")

# Read in strategy csv
table = load_from_csv(cumulative_regret_file_path)

'''
# Overall stats
num_info_sets = len(table)
num_visited = 0
for info_set in table.keys():
    if sum(table[info_set].values()) > 0:
        num_visited += 1
'''

# never fold good hands (make cumulative regret large negative)

# TODO: there are some impossible and some missing buckets here due to how we constructed ranges, i.e:
#       preflop pair (~10) --> flop straight (9) is impossible
#       flop high card (2) --> turn high card (1) is missing
HOLE_THRESHOLD = 9 # hole pair/good hole cards (buckets 9-10?
THRESHOLD = 10 # sufficiently high strength at any point starting on flop
for bounty in range(2):
    for my_stack in range(10):
        for opp_stack in range(10):
            for preflop in range(11):
                if preflop >= HOLE_THRESHOLD:
                    # TODO: maybe should consider stacks/whether opponent has raised a lot, which is what latest strategy seems to do in some cases
                    hashable_info_set = '|'.join((str(bounty), str(preflop), '0|0|0', str(my_stack), str(opp_stack)))
                    if hashable_info_set in table:
                        table[hashable_info_set][FOLD] = -LARGE_REGRET

                for flop in range(11):
                    if flop >= THRESHOLD:
                        hashable_info_set = '|'.join((str(bounty), str(preflop), str(flop), '0|0', str(my_stack), str(opp_stack)))
                        if hashable_info_set in table:
                            table[hashable_info_set][FOLD] = -LARGE_REGRET

                    for turn in range(flop, 11):
                        if turn >= THRESHOLD:
                            hashable_info_set = '|'.join((str(bounty), str(preflop), str(flop), str(turn), '0', str(my_stack), str(opp_stack)))
                            if hashable_info_set in table:
                                table[hashable_info_set][FOLD] = -LARGE_REGRET

                        for river in range(THRESHOLD, 11):
                            hashable_info_set = '|'.join((str(bounty), str(preflop), str(flop), str(turn), str(river), str(my_stack), str(opp_stack)))
                            if hashable_info_set in table:
                                table[hashable_info_set][FOLD] = -LARGE_REGRET


# always fold on bad hands (make cumulative regret large positive)
# hole bucket 0?

# save new cumulative regret csv
save_directory = '.'
save_to_csv(f'{save_directory}/manual_cumulative_regret.csv', table)