'''
Simple example pokerbot, written in Python.
'''
from python_skeleton.skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from python_skeleton.skeleton.states import GameState, TerminalState, RoundState
from python_skeleton.skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from python_skeleton.skeleton.bot import Bot
from python_skeleton.skeleton.runner import parse_args, run_bot

from python_skeleton.calculate_winrates import *

import random
import math
import eval7

class History(RoundState):
    '''
    Representation of history in poker game for CFR training.
    Based on RoundState (states.h) used in Pokerbots cpp_skeleton

    TODO: implement methods (maybe replace params with RoundState param, TBD)
    TODO: make sure we have plan for structure of sigma_t and
      how to efficiently get/update sigma_t(I, a) (was thinking maybe std::hash)

    @param active Either 0 or 1 to indicate the active player
    @param...
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.active = 0 # 0 or 1
        # RoundState: ['button', 'street', 'pips', 'stacks', 'hands', 'bounties', 'deck', 'previous_state']

    def generateInitialNode():
       '''
       Return History representative of beginning of round
       '''

    def  getNodeType():
       '''
       Returns char denoting current round state:
         'T': terminal
         'C': chance
         'D': decision
       '''
    
    def getPayout(playerId):
       '''
       Returns utility of respective player if state is terminal node

        @param playerId
       '''

    def generateChanceOutcome():
       '''
       Returns new History representative of sampling an outcome if state is chance node
       '''

    def getLegalActions(playerId):
       '''
       Returns array of legal actions for active player if state is decision node
         - could use an array of bool flags? (10 elements for 10 action buckets)
         - TODO: this function exists in roundState, so funciton would just exist to reformat
       
        @param playerId
       '''
    
    def generateActionOutcome(playerId, action):
       '''
       Returns new History representative of player doing action on current history

        @param playerId
        @param action (use same abbreviations as run() in runner.py)
       '''

    def getPlayerInfo(playerId):
       '''
       Returns information set for input player to use in CFR algorithm
       '''
