from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import TerminalState, RoundState
from skeleton.states import STARTING_STACK, BIG_BLIND, SMALL_BLIND
from buckets import get_bucket
from calculate_winrates import load_hole_winrates

from information_set import InformationSet

import random
import math
import eval7

RAISES = [20, 40, 80]
NUM_ACTIONS = 4 + len(RAISES)
BOUNTY_RATIO = 1.5
BOUNTY_CONSTANT = 10

class History():
    '''
    Representation of history in poker game for CFR training.
    Based on RoundState (states.py) used in Pokerbots python skeleton.

    @param active Either 0 or 1 to indicate the active player
    @param roundState Representation of round state used by states.py and runner.py
        TODO: can maybe use engine.py? figure out engine.py vs states.py
    @param in_deck List representing input community cards (round_state has in_hand player 0 cards in this case)
    '''

    def __init__(self, active, round_state, set_deck=None):
        self.set_deck = set_deck
        self.active = active # 0 or 1
        self.round_state = round_state
        self.hole_winrates = load_hole_winrates('python_skeleton/hole_winrates.csv')
        # RoundState: ['button', 'street', 'pips', 'stacks', 'hands', 'bounties', 'deck', 'previous_state']

    @classmethod
    def generate_initial_node(cls, start_player, set_cards=None, set_buckets=None):
        '''
        Return History representative of beginning of round

        @param set_cards List of specific cards to play this round ([0:2] player, [2:7] community)
        @param set_buckets Gives bucket in form of string: 'bounty|preflop|flop|turn|river'
        '''

        # pick bounties at random
        bounty_chars = [str(i) for i in range(2, 10)] + ['T', 'J', 'Q', 'K', 'A']
        bounties = [bounty_chars[random.randint(0, 12)], bounty_chars[random.randint(0, 12)]]

        # set stacks and set pips based on start player
        pips = [SMALL_BLIND, BIG_BLIND] if start_player == 0 else [BIG_BLIND, SMALL_BLIND]
        stacks = [STARTING_STACK - pips[0], STARTING_STACK - pips[1]]
        deck = [] # unlike engine structure, we fill this as we reach chance nodes

        full_deck = eval7.Deck()
        full_deck.shuffle()
        
        if set_cards or set_buckets:
            if set_buckets:
                # choose representative list of 2 player + 5 community cards
                flags = set_buckets.split('|')

                # TODO: actually make this work lol; for now should error

                bounty = int(flags[0])
                preflop = int(flags[1])
                flop = int(flags[2])
                turn = int(flags[3])
                river = int(flags[4])

            assert len(set_cards) == 7

            for card in set_cards:
                full_deck.cards.remove(eval7.Card(card))

            # set player 0's cards based on input and player 1's cards random
            hand0 = set_cards[:2]
            hand1 = [str(card) for card in full_deck.deal(2)]
            hands = [hand0, hand1]
            set_deck = set_cards[2:]
        
        else:
            # deal two hands at random
            hand0 = [str(card) for card in full_deck.deal(2)]
            hand1 = [str(card) for card in full_deck.deal(2)]
            hands = [hand0, hand1]
            set_deck = None

        round_state = RoundState(0, 0, pips, stacks, hands, bounties, deck, None)
        return History(start_player, round_state, set_deck)

    def get_active_player(self):
        '''
        Return ID of active player (either 0 or 1)
        '''
        return self.active

    def get_node_type(self):
        '''
        Returns char denoting current round state:
          'T': terminal
          'C': chance
          'D': decision
        '''
        if isinstance(self.round_state, TerminalState):
            return 'T'
        elif self.round_state.street != len(self.round_state.deck): # proceed_street was just called
            return 'C'
        else:
            return 'D'
    
    def get_utility(self, player_id, dual_learning=False):
        '''
        Returns utility of respective player if state is terminal node

        @param player_id Either 0 or 1
        '''
        assert isinstance(self.round_state, TerminalState)

        deltas = self.round_state.deltas
        bounty_hits = self.round_state.bounty_hits

        # terminal state is result of showdown, not fold, we need to calculate delta and bounty hits
        if bounty_hits == None:
            previous_state = self.round_state.previous_state
            hand0 = [eval7.Card(s) for s in previous_state.hands[0] + previous_state.deck]
            hand1 = [eval7.Card(s) for s in previous_state.hands[1] + previous_state.deck]
            score0 = eval7.evaluate(hand0)
            score1 = eval7.evaluate(hand1)
            if score0 > score1:
                delta = self.get_delta(0)
            elif score0 < score1:
                delta = self.get_delta(1)
            else:
                # split the pot
                delta = self.get_delta(2)
        else:
            delta = self.get_delta(1 if deltas[0] > deltas[1] else 0)
        
        # return utility of both players as opposed to just input player
        if dual_learning:
            return (delta, -delta)
        
        return delta if player_id == 0 else -delta

    def get_delta(self, winner_index: int) -> int: # copy paste from engine.py
        '''Returns the delta after bounty rules are applied.

        Args:
            winner_index (int): Index of the winning player. Must be 0 (player A),
                1 (player B), or 2 (split pot).

        Returns:
            int: The delta value after applying bounty rules.
        '''
        assert winner_index in [0, 1, 2]
        assert isinstance(self.round_state, TerminalState)
        state = self.round_state.previous_state

        bounty_hit_0, bounty_hit_1 = state.get_bounty_hits()

        delta = 0
        if winner_index == 2:
            # Case of split pots
            assert(state.stacks[0] == state.stacks[1]) # split pots only happen on the river + equal stacks
            delta = STARTING_STACK - state.stacks[0]
            if bounty_hit_0 and not bounty_hit_1:
                delta = delta * (BOUNTY_RATIO - 1) / 2 + BOUNTY_CONSTANT
            elif not bounty_hit_0 and bounty_hit_1:
                delta = -(delta * (BOUNTY_RATIO - 1) / 2 + BOUNTY_CONSTANT)
            else:
                delta = 0
        else:
            # Case of one player winning
            if winner_index == 0:
                delta = STARTING_STACK - state.stacks[1]
                if bounty_hit_0:
                    delta = delta * BOUNTY_RATIO + BOUNTY_CONSTANT
            else:
                delta = state.stacks[0] - STARTING_STACK
                if bounty_hit_1:
                    delta = delta * BOUNTY_RATIO - BOUNTY_CONSTANT

        # if delta is not an integer, round it down or up depending on who's in position
        if abs(delta - math.floor(delta)) > 1e-6:
            delta = math.floor(delta) if state.button % 2 == 0 else math.ceil(delta)
        return int(delta)

    def generate_chance_outcome(self):
        '''
        Returns new History representative of sampling an outcome if state is chance node
        '''

        # update community cards (deck)
        if self.set_deck:
            new_deck = self.set_deck[:self.round_state.street] # reveal cards based on pre-set deck
        else:
            # get deck of remaining cards
            full_deck = eval7.Deck()
            full_deck.shuffle()

            dealt_cards = self.round_state.hands[0] + self.round_state.hands[1] + self.round_state.deck
            for card in dealt_cards:
                full_deck.cards.remove(eval7.Card(card))

            # reveal new community cards at random
            new_deck = list(self.round_state.deck)
            if self.round_state.street == 3:
                for _ in range(3):
                    new_deck.append(str(full_deck.cards.pop()))
            else:
                new_deck.append(str(full_deck.cards.pop()))

        new_pips = list(self.round_state.pips)
        new_stacks = list(self.round_state.stacks)
        state = RoundState(1, self.round_state.street, new_pips, new_stacks, self.round_state.hands, self.round_state.bounties, new_deck, self.round_state)
        return History(1, state, self.set_deck) # active = button % 2

    def get_legal_actions(self):
        '''
        Returns 1xNUM_ACTIONS array representing NUM_ACTIONS action buckets for active player, where indexed value is:
            True if action is legal
            False if action is not legal

        Actions:
            0  - Fold
            1  - Call
            2  - Check
            3  - All In
            4+ - Raises
        '''
        output = [False for _ in range(NUM_ACTIONS)]

        legal_actions = self.round_state.legal_actions()
        min_raise, max_raise = self.round_state.raise_bounds()

        for i, action in enumerate((FoldAction, CallAction, CheckAction)):
            if action in legal_actions:
                output[i] = True

        if RaiseAction in legal_actions:
            output[3] = True

            for i, bet in enumerate(RAISES):
                if min_raise < bet and max_raise > bet:
                    output[i+4] = True

        return output
    
    def generate_action_outcome(self, action_index):
        '''
        Returns new History representative of player doing action on current history

        @param player_id
        @param action Action of input player as follows:
            0  - Fold
            1  - Call
            2  - Check
            3  - All In
            4+ - Raises
        '''

        min_raise, max_raise = self.round_state.raise_bounds()
        actions = [FoldAction, CallAction, CheckAction, max_raise] + RAISES

        # sb call bb
        if action_index == 1 and self.round_state.button == 0:
            rs = RoundState(1, 3, [BIG_BLIND] * 2, [STARTING_STACK - BIG_BLIND] * 2, self.round_state.hands, self.round_state.bounties, self.round_state.deck, self.round_state)
            return History(1-self.active, rs, self.set_deck)

        # TODO: should maybe check if input action is legal when debugging
        if action_index < 3:
            return History(1-self.active, self.round_state.proceed(actions[action_index]()), self.set_deck)
        else:
            return History(1-self.active, self.round_state.proceed(RaiseAction(actions[action_index])), self.set_deck)

    def get_player_info(self, player_id):
        '''
        Returns information set for input player to use in CFR algorithm
        '''
        rs = self.round_state
        bucket = get_bucket(rs.hands[player_id] + rs.deck, self.round_state.bounties[player_id], self.hole_winrates)

        return InformationSet(bucket, rs.stacks[player_id], rs.stacks[1 - player_id])

    def __str__(self):
        if isinstance(self.round_state, TerminalState):
            return 'Deltas: ' + str(self.round_state.deltas) + '\nBounty Hits: ' + str(self.round_state.bounty_hits) + "\n_____________"
        return 'Active: ' + str(self.active) +'\nButton: ' + str(self.round_state.button) + '\nStreet: ' + str(self.round_state.street) + '\nPips: ' + str(self.round_state.pips)  + '\nStacks: ' + str(self.round_state.stacks)  + '\nHands: ' + str(self.round_state.hands)  + '\nBounties: ' + str(self.round_state.bounties)  + '\nCommunity: ' + str(self.round_state.deck) + "\n_____________"

# if __name__ == '__main__':
#     set_cards = ['As', 'Ks', 'Qs', 'Js', 'Ts', '2d', '2c']
#     rs = History.generate_initial_node(0)
#     print(rs)
#     print(rs.get_node_type())
    
#     # pre-flop
#     rs = rs.generate_action_outcome(1) # call
#     print(rs)
#     print(rs.get_node_type())

#     rs = rs.generate_chance_outcome()
#     print(rs)
#     print(rs.get_node_type())

#     # post-flop
#     rs = rs.generate_action_outcome(2) # check
#     print(rs)
#     print(rs.get_node_type())
#     rs = rs.generate_action_outcome(2) # check
#     print(rs)
#     print(rs.get_node_type())

#     rs = rs.generate_chance_outcome()
#     print(rs)
#     print(rs.get_node_type())

#     # turn
#     rs = rs.generate_action_outcome(2) # check
#     print(rs)
#     print(rs.get_node_type())
#     rs = rs.generate_action_outcome(2) # check
#     print(rs)
#     print(rs.get_node_type())

#     rs = rs.generate_chance_outcome()
#     print(rs)
#     print(rs.get_node_type())
    
#     # river
#     rs = rs.generate_action_outcome(2) # check
#     print(rs)
#     print(rs.get_node_type())
#     rs = rs.generate_action_outcome(2) # check
#     print(rs)
#     print(rs.get_node_type())


