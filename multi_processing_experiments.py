import multiprocessing as mp
from time import sleep
from random import random

class Trainer:
    def __init__(self):
        self.data = {
            0: 0,
            1: 0
        }
        self.locks = None

    def algo(self, player, t):
        player = 1
        sleep(random())    
        with self.locks[player]:
            sleep(random())
            self.data[player] += 1
        print(f'Player {player} says hello from iter {t}')

    def solve(self, iters, multi_processing=True):
        num_cores = mp.cpu_count()
        if multi_processing and num_cores > 1:
            print(f'Setting up dict managers...')
            manager = mp.Manager()
            self.data = manager.dict(self.data)
            self.locks = manager.dict({
                0: manager.Lock(),
                1: manager.Lock()
            })

            print(f'Parallel training with {num_cores} cpu cores...')
            parallelization_factor = num_cores // 2
            for iter in range(0, iters, parallelization_factor):
                processes = [
                    mp.Process(target=self.algo, args=(player, t)) 
                    for player in [0, 1]
                    for t in range(iter, min(iters, iter + parallelization_factor))
                ]

                print('Starting processes...')
                for process in processes:
                    process.start()

                print('Waiting for processes...')
                for process in processes:
                    process.join()

                print('Done with one cycle...')

            print(f'Closing dict managers...')
            self.data = dict(self.data)
            self.locks = None

        else:
             print('Training sequentially...')
             for t in range(iters):
                for player in [0, 1]:
                    self.algo(player, t)


if __name__ == '__main__':
    trainer = Trainer()
    trainer.solve(100)
    print(trainer.data)
