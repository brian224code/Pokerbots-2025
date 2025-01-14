#include <skeleton/actions.h>
#include <skeleton/constants.h>
#include <skeleton/runner.h>
#include <skeleton/states.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include <map>
#include <string>
#include <array>
#include <time.h>

using namespace pokerbots::skeleton;

const char RANKS[13] = {'2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'};
const char SUITS[4] = {'h', 's', 'c', 'd'};
const int NUMBUCKETS = 10;
const float PREFLOPRANGES = {0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0};
const float FLOPRANGES = {0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0};
const float TURNRANGES = {0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0};
const float RIVERRANGES = {0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0};
struct Bucket {
  bool bounty = false;
  int preflop = 0;
  int flop = 0;
  int turn = 0;
  int river = 0;
};
const std::map<std::string, float> HOLEWINRATES;




/*
  Takes in poker hand as a std::string, e.g. '4c2sAc7h6d'

  Returns 0 if hand is not low strength / high potential.
  Returns 1 if hand is highcard + straight/flush draw
  Returns 2 if hand is pair + straight/flush draw
*/
int isHighPotential(std::string hand) {
  
  Evaluator evaluator = Evaluator();

  std::string currentHand = evaluator.eval(hand);

  if (currentHand == 'high' || currentHand == 'pair') {
    for (int i = 0; i < 4; i++) {
      if (evaluator.handType(hand + '2' + SUITS[i]) == 'flush') {
        return currentHand == 'pair'? 2 : 1;
      }
    }
    for (int i = 0; i < 13; i++) {
      if (evaluator.handType(hand + SUITS[i] + 'h') == 'straight') {
        return currentHand == 'pair'? 2 : 1;
      }
    }
  }

  return 0;
}

/*
  Takes in poker hand as a std::string, e.g. '4c2sAc7h6d'
  and bounty as a char, e.g. '4' or 'K'

  Returns a Bucket struct
*/
int getBucket(std::string hand, char bounty) {
  
  int numCards = hand.length() / 2;
  if (!(numCards > 4 && numCards < 8) && numCards != 2) {
    throw std::invalid_argument('Hand must have 2,5,6,7 cards.');
  }

  Evaluator evaluator = Evaluator();

  Bucket bucket;

  if (hand.find(bounty) != std::string::npos) {
   bucket.bounty = 1; 
  }
  if (numCards >= 2) {
    std::string currentHand = hand.substr(0, 4);
    
  }
  if (numCards >= 5) {
    std::string currentHand = hand.substr(0, 10);
    int potential = isHighPotential(currentHand);
    if (potential) {
      bucket.flop = NUMBUCKETS + potential
    } else {
      int score = evaluator.eval(currentHand);
      for (int i = 0; i < NUMBUCKETS; i++) {
        if (score <= FLOPRANGES[i]) {
          bucket.flop = i + 1;
          break;
        }
      }
      if (!bucket.flop) {
        bucket.flop = 10;
      }
    }
  }
  if (numCards >= 6) {
    std::string currentHand = hand.substr(0, 12);
    int potential = isHighPotential(currentHand);
    if (potential) {
      bucket.turn = NUMBUCKETS + potential
    } else {
      int score = evaluator.eval(currentHand);
      for (int i = 0; i < NUMBUCKETS; i++) {
        if (score <= TURNRANGES[i]) {
          bucket.turn = i + 1;
          break;
        }
      }
      if (!bucket.turn) {
        bucket.turn = 10;
      }
    }
  }
  if (numCards == 7) {
    std::string currentHand = hand.substr(0, 14);
    int score = evaluator.eval(currentHand);
    for (int i = 0; i < NUMBUCKETS; i++) {
      if (score <= RIVERRANGES[i]) {
        bucket.river = i + 1;
        break;
      }
    }
    if (!bucket.river) {
      bucket.river = 10;
    }
  }
  
  return bucket;
}

struct Bot {
  /*
    Called when a new round starts. Called NUM_ROUNDS times.

    @param gameState The GameState object.
    @param roundState The RoundState object.
    @param active Your player's index.
  */
  void handleNewRound(GameInfoPtr gameState, RoundStatePtr roundState,
                      int active) {
    // int myBankroll = gameState->bankroll;  // the total number of chips you've gained or lost from the beginning of the game to the start of this round 
    // float gameClock = gameState->gameClock;  // the total number of seconds your bot has left to play this game 
    // int roundNum = gameState->roundNum;  // the round number from 1 to State.NUM_ROUNDS 
    // auto myCards = roundState->hands[active];  // your cards 
    // bool bigBlind = (active == 1);  // true if you are the big blind
  }

  /*
    Called when a round ends. Called NUM_ROUNDS times.

    @param gameState The GameState object.
    @param terminalState The TerminalState object.
    @param active Your player's index.
  */
  void handleRoundOver(GameInfoPtr gameState, TerminalStatePtr terminalState,
                       int active) {
    // int myDelta = terminalState->deltas[active];  // your bankroll change from this round 
    auto previousState = std::static_pointer_cast<const RoundState>(terminalState->previousState);  // RoundState before payoffs
    // int street = previousState->street;  // 0, 3, 4, or 5 representing when this round ended 
    // auto myCards = previousState->hands[active];  // your cards 
    // auto oppCards = previousState->hands[1-active];  // opponent's cards or "" if not revealed 
    
    bool myBountyHit = terminalState->bounty_hits[active];  // true if your bounty hit this round
    bool oppBountyHit = terminalState->bounty_hits[1-active];  // true if your opponent's bounty hit this round

    char bounty_rank = previousState->bounties[active];  // your bounty rank

    // The following is a demonstration of accessing illegal information (will not work)
    char opponent_bounty_rank = previousState->bounties[1-active];  // attempting to grab opponent's bounty rank
    if (myBountyHit) {
      std::cout << "I hit my bounty of " << bounty_rank << "!" << std::endl;
    }
    if (oppBountyHit) {
      std::cout << "Opponent hit their bounty of " << opponent_bounty_rank << "!" << std::endl;
    }
  }

  /*
    Where the magic happens - your code should implement this function.
    Called any time the engine needs an action from your bot.

    @param gameState The GameState object.
    @param roundState The RoundState object.
    @param active Your player's index.
    @return Your action.
  */
  Action getAction(GameInfoPtr gameState, RoundStatePtr roundState,
                   int active) {
    auto legalActions =
        roundState->legalActions(); // the actions you are allowed to take
    int street = roundState->street;  // 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
    auto myCards = roundState->hands[active];  // your cards 
    auto boardCards = roundState->deck;  // the board cards 
    int myPip = roundState->pips[active];  // the number of chips you have contributed to the pot this round of betting 
    int oppPip = roundState->pips[1-active]; // the number of chips your opponent has contributed to the pot this round of betting 
    int myStack = roundState->stacks[active];  // the number of chips you have remaining 
    int oppStack = roundState->stacks[1-active];  // the number of chips your opponent has remaining 
    int continueCost = oppPip - myPip;  // the number of chips needed to stay in the pot
    int myContribution = STARTING_STACK - myStack;  // the number of chips you have contributed to the pot 
    int oppContribution = STARTING_STACK - oppStack;  // the number of chips your opponent has contributed to the pot
    char myBounty = roundState->bounties[active];  // your current bounty rank 

    int minCost = 0, maxCost = 0;
    std::array<int, 2> raiseBounds = {0, 0};
    if (legalActions.find(Action::Type::RAISE) != legalActions.end()) {
      raiseBounds = roundState->raiseBounds();  // the smallest and largest numbers of chips for a legal bet/raise 
      minCost = raiseBounds[0] - myPip;  // the cost of a minimum bet/raise 
      maxCost = raiseBounds[1] - myPip;  // the cost of a maximum bet/raise
    }

    if (legalActions.find(Action::Type::RAISE) != legalActions.end()) {
      if (rand() % 2 == 0) {
        return {Action::Type::RAISE, raiseBounds[0]};
      }
    }
    if (legalActions.find(Action::Type::CHECK) != legalActions.end()) {
      return {Action::Type::CHECK};
    }
    if (rand() % 4 == 0) {
      return {Action::Type::FOLD};
    }
    return {Action::Type::CALL};
  }
};

/*
  Main program for running a C++ pokerbot.
*/
int main(int argc, char *argv[]) {
  srand(time(NULL));
  auto [host, port] = parseArgs(argc, argv);
  runBot<Bot>(host, port);
  return 0;
}
