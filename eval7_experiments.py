import eval7
from matplotlib import pyplot as plt
import pandas as pd

def test_eval7_scores():
    while True:
        print('------------------------------')
        hand = input('Hand: ')

        hand = [eval7.Card(s) for s in hand.split(' ')]

        score = eval7.evaluate(hand)

        handtype = eval7.handtype(score)

        print('Score: ', score)
        print('Handtype: ', handtype)

def plot_winrate_histogram(filename):
    df = pd.read_csv(filename)
    
    data = [row['winrate'] for _, row in df.iterrows()]

    plt.hist(data, bins=500)
    plt.xlabel('Winrates')
    plt.ylabel('Frequency')
    plt.title('Winrate Histogram')
    plt.show()

def divide_winrates(filename, divisions):
    df = pd.read_csv(filename)
    
    data = [row['winrate'] for _, row in df.iterrows()]
    data.sort()

    size_of_bucket = len(data) // divisions
    threshholds = []
    for i in range(0, len(data), size_of_bucket):
        threshholds.append(data[i])

    return threshholds


if __name__ == '__main__':
    test_eval7_scores()
    # print(divide_winrates('./all_hole_winrates.csv', 10))
    # plot_winrate_histogram('./all_hole_winrates.csv')