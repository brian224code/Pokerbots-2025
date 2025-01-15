import eval7
from calculate_winrates import load_hole_winrates

class Bucket:
    def __init__(self):
        self.bounty = 0
        self.preflop = 0
        self.flop = 0
        self.turn = 0
        self.river = 0

    def __str__(self):
        return ('\nbounty: ' + str(self.bounty) + 
                '\npreflop: ' + str(self.preflop) + 
                '\nflop: ' + str(self.flop) + 
                '\nturn: ' + str(self.turn) + 
                '\nriver: ' + str(self.river) + '\n')

def is_high_potential(eval7_hand):
    """
    Arguments:
        hand: list of cards in eval7 format
    
    Returns:
        0 if hand is not low-strength-high-potential
        1 if hand is High Card and a Straight/Flush draw
        2 if hand is Pair and a Straight/Flush draw
    """
    handtype = eval7.handtype(eval7.evaluate(eval7_hand))

    deck = eval7.Deck()
    for card in eval7_hand:
        deck.cards.remove(card)

    if handtype == 'Pair' or handtype == 'High Card':
        for card in deck:
            newHandtype = eval7.handtype(eval7.evaluate(eval7_hand + [card]))
            if newHandtype == 'Flush' or newHandtype == 'Straight':
                return 2 if handtype == 'Pair' else 1

    return 0

def get_bucket(hand, bounty, hole_winrates):
    """
    Arguments:
        hand; list of cards in string format
        bounty: rank of current bounty
        hole_winrates: dictionary of hole winrates from csv
    
    Returns:
        Bucket for current hand
    """
    if len(hand) not in [2,5,6,7]:
        raise Exception('Hand must have 2,5,6,7 cards.')

    NUM_BUCKETS = 10
    PREFLOP_RANGES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    EVAL7_SCORE_RANGE = [0, 135004160]
    FLOP_RANGES = [(EVAL7_SCORE_RANGE[1] / 10.0) * (i+1) for i in range(10)]
    TURN_RANGES = [(EVAL7_SCORE_RANGE[1] / 10.0) * (i+1) for i in range(10)]
    RIVER_RANGES = [(EVAL7_SCORE_RANGE[1] / 10.0) * (i+1) for i in range(10)]

    bucket = Bucket()

    # Calculate bounty bucket
    if bounty in ''.join(hand):
        bucket.bounty = 1

    # Calculate preflop bucket
    rank_1 = hand[0][0]
    rank_2 = hand[1][0]
    suited = '1' if hand[0][1] == hand[1][1] else '0'

    if rank_1 + rank_2 + suited in hole_winrates:
        hole_winrate = hole_winrates[rank_1 + rank_2 + suited]
    else:
        hole_winrate = hole_winrates[rank_2 + rank_1 + suited]

    for i, threshhold in enumerate(PREFLOP_RANGES):
        if hole_winrate <= threshhold:
            bucket.preflop = i + 1
            break

    # Calculate flop bucket
    if len(hand) >= 5:
        current_hand = [eval7.Card(card) for card in hand[:5]]
        potential = is_high_potential(current_hand)
        if potential:
            bucket.flop = NUM_BUCKETS + potential
        else:
            score = eval7.evaluate(current_hand)
            for i, threshhold in enumerate(FLOP_RANGES):
                if score <= threshhold:
                    bucket.flop = i + 1
                    break
    # Calculate turn bucket
    if len(hand) >= 6:
        current_hand.append(eval7.Card(hand[5]))
        potential = is_high_potential(current_hand)
        if potential:
            bucket.turn = NUM_BUCKETS + potential
        else:
            score = eval7.evaluate(current_hand)
            for i, threshhold in TURN_RANGES:
                if score <= threshhold:
                    bucket.turn = i + 1
                    break
    # Calculate river bucket
    if len(hand) == 7:
        current_hand.append(eval7.Card(hand[6]))
        score = eval7.evaluate(current_hand)
        for i, threshhold in enumerate(RIVER_RANGES):
            if score <= threshhold:
                bucket.river = i + 1
                break
    
    return bucket

if __name__ == '__main__':
    hand = ['Ac', 'Kd', '2c', '3c', '4d', 'Kh']
    bounty = '2'
    hole_winrates = load_hole_winrates('hole_winrates.csv')
    print(get_bucket(hand, bounty, hole_winrates))
