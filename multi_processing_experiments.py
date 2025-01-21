import multiprocessing as mp
import queue
import os
from time import sleep
from random import random

class Trainer:
    def __init__(self):
        self.data = {}
        self.locks = {}

    def algo(self, player, t, q):
        sleep(random())    
        if player not in self.locks:
            q.put(player)
            sleep(random())
        with self.locks[player]:
            sleep(random())
            if player not in self.data:
                self.data[player] = 0
            self.data[player] += 1
        print(f'Player {player} says hello from iter {t}')

    def solve(self, iters, players=2):
        num_cores = os.process_cpu_count()
        print(f'Setting up dict managers...')
        manager = mp.Manager()
        self.data = manager.dict(self.data)
        self.locks = manager.dict(self.locks)
        q = mp.Queue(maxsize=1)
        

        print(f'Parallel training with {num_cores} cpu cores...')
        parallelization_factor = num_cores // players
        for iter in range(0, iters, parallelization_factor):
            processes = [
                mp.Process(target=self.algo, args=(player, t, q)) 
                for player in range(players)
                for t in range(iter, min(iters, iter + parallelization_factor))
            ]

            print('Starting processes...')
            for process in processes:
                process.start()

            print('Waiting for processes...')

            while any(map(lambda process: process.is_alive(), processes)):
                try:
                    new_bucket = q.get(block=False)
                    print(f'Adding new bucket: {new_bucket}')
                    self.locks[new_bucket] = manager.Lock()
                except queue.Empty:
                    pass

            print('Done with one cycle...')

        print(f'Closing dict managers...')
        self.data = dict(self.data)
        self.locks = dict(self.data)
        q.close()


if __name__ == '__main__':
    trials = 10
    iters = 100
    buckets = 8
    correct = 0
    for trial in range(trials):
        print('=======================================================')
        print(f'Starting trial {trial}...')
        trainer = Trainer()
        trainer.solve(iters, buckets)
        if all(map(lambda bucket: bucket == iters, trainer.data.values())):
            correct += 1
    print(f'Overall correctness: {float(correct) / trials}')
