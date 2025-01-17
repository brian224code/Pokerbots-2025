import matplotlib.pyplot as plt
import csv

# We want to regret not taking good actions more and bad actions less, so how do we actually want to view this
def plot_regrets(filename):
    average_regrets = []

    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            regrets = row
            for i in range(len(regrets)):
                if (i+1) % 10 == 0:
                    average_regrets.append(sum([float(regret) for regret in regrets[i-9:i+1]]) / 10)
                    
    plt.plot(average_regrets, color='b')
    plt.title('10-Averaged Regrets over time')
    plt.xlabel('Time')
    plt.ylabel('Regret')
    plt.grid(True)
    plt.show()

if __name__ == '__main__':
    plot_regrets('./CFR_TRAIN_DATA/1.16/regrets.csv')