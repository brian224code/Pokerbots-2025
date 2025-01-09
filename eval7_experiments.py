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




if __name__ == '__main__':
    # test_eval7_scores()
    plot_winrate_histogram('./python_skeleton/winrates_for_street_size_0.csv')
