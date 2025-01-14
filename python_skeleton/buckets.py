import eval7

def isHighPotential(eval7_hand):
    """
    Arguments:
        hand: list of cards in eval7 format
    
    Returns:
        0 if hand is not low-strength-high-potential
        1 if hand is High Card and a Straight/Flush draw
        2 if hand is Pair and a Straight/Flush draw
    """
    handtype = eval7.handtype(eval7.evaluate(eval7_hand))

    if handtype == 'Pair' or handtype == 'High Card':
        for card in ['2h', '3d', '4s', '5c', '6h', '7h', '8h', '9h', 'Th', 'Jh', 'Qh', 'Kh', 'Ah']:
            newHandtype = eval7.handtype(eval7.evaluate(eval7_hand + [eval7.Card(card)]))
            if newHandtype == 'Flush' or newHandtype == 'Straight':
                return 2 if handtype == 'Pair' else 1

    return 0

class Bucket:
    def __init___(self):
        self.bounty = 0
        self.preflop = 0
        self.flop = 0
        self.turn = 0
        self.river = 0
    


def getBucket(hand, bounty, hole_winrates):
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

    for i, threshhold in PREFLOP_RANGES:
        if hole_winrate <= threshhold:
            bucket.preflop = i + 1
            break

    # Calculate flop bucket
    if len(hand) >= 5:
        current_hand = [eval7.Card(card) for card in hand[:5]]
        potential = isHighPotential(current_hand)
        if potential:
            bucket.flop = NUM_BUCKETS + potential
        else:
            score = eval7.evaluate(current_hand)
            for i, threshhold in FLOP_RANGES:
                if score <= threshhold:
                    bucket.flop = i + 1
                    break
    # Calculate turn bucket
    if len(hand) >= 6:
        current_hand.append(eval7.Card(hand[5]))
        potential = isHighPotential(current_hand)
        if potential:
            bucket.flop = NUM_BUCKETS + potential
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
        for i, threshhold in RIVER_RANGES:
            if score <= threshhold:
                bucket.turn = i + 1
                break
    
    return bucket

if __name__ == '__main__':
    print(isHighPotential(['7h', '8c', '9d', '9c', 'Tc']))