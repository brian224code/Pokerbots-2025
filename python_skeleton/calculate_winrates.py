import eval7
import csv
import os
import itertools
from math import comb
import pandas as pd
from tqdm import tqdm

def monte_carlo(visible_cards, iters):
    """
    Calculates win probability given your hole and current community cards

    Args:
        visible_cards: list of 2 hole cards + current community cards
        iters: num iterations to sim

    Returns:
        winrate
    """
    deck = eval7.Deck()

    visible_cards = [eval7.Card(card) for card in visible_cards]
    my_hole = visible_cards[:2]
    current_community_cards = visible_cards[3:]

    num_community_cards_to_draw = 5 - len(current_community_cards)

    for card in visible_cards:
        deck.cards.remove(card)

    win_count = 0.0

    for _ in range(iters):
        deck.shuffle()

        hidden_cards = deck.peek(2 + num_community_cards_to_draw)
        opp_hole = hidden_cards[:2]
        community_cards = current_community_cards + hidden_cards[3:]

        my_score = eval7.evaluate(my_hole + community_cards)
        opp_score = eval7.evaluate(opp_hole + community_cards)

        if my_score > opp_score:
            win_count += 1
        elif my_score == opp_score:
            win_count += 0.5

    return win_count / iters

def make_csv(num_community_cards, iters):
    """
    Create lookup table of winrates for hands in a given stage in the round

    Args:
        num_community_cards: 0 for preflop, 3 for flop, 4 for turn, 5 for river
        iters: number of sims to run when calculating winrates

    Returns:
        nothing (saves lookup table as a csv)
    """
    if num_community_cards not in [0, 3, 4, 5]:
        raise Exception('Valid num_community_cards are 0 for preflop, 3 for flop, 4 for turn, 5 for river.')
    
    deck = eval7.Deck()
    holes = itertools.combinations(deck, 2 + num_community_cards)
    total_hands = comb(52, 2 + num_community_cards)
    winrates = []

    for hole in tqdm(holes, desc="Simulating", unit="iteration", total=total_hands):
        hole = [str(card) for card in hole]
        winrate = monte_carlo(hole, iters)

        row = {
            'community ' + str(1 + card): hole[2 + card]
            for card in range(num_community_cards)
            }
        
        row['hole 1'] = hole[0]
        row['hole 2'] = hole[1]
        row['winrate'] = winrate

        winrates.append(row)

    with open('./winrates_for_street_size_' + str(num_community_cards) + '.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[field for field in winrates[0].keys()])
        writer.writeheader()
        writer.writerows(winrates)

def load_csv(filename):
    """
    Reads csv lookup table

    Args:
        filename: name of file to parse
    
    Returns
        dictionary where the keys are frozensets of the visible hand and the values are winrates
    """
    df = pd.read_csv(filename)

    lookup_table = {
        frozenset([row[card] for card in df.columns if card != 'winrate']): row['winrate']
        for _, row in df.iterrows()
    }

    return lookup_table

if __name__ == "__main__":
    make_csv(0, 100000)
