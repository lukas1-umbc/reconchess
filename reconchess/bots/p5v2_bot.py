import random
import pprint
from reconchess import *

#Dictionary to make it easy/possible to index with the probability distributions.
#e.g. getIndex("king") will return the king's index in a given square's probability distribution list.
#This works as long as we initialize the structure correctly.
#An explanation for these indexes and how the probability ditribution works with them can be found here:
#https://imgur.com/a/zRJgRnf
def getIndex(pieceName):
    pieceIndexer = {
        "rook1": 0, "knight1": 1, "bishop1": 2, 
        "queen": 3, "king": 4,
        "bishop2": 5, "knight2": 6, "rook2": 7,
        "pawn1": 8, "pawn2": 9, "pawn3": 10, "pawn4": 11, "pawn5": 12, "pawn6": 13, "pawn7": 14, "pawn8": 15
    }
    return pieceIndexer[pieceName]

#initializes the 3D list we use to keep the probability distributions of each square
def initDist():
    #8x8x16 list
    distList = [[ [0 for dist in range(16)] for row in range(8)] for col in range(8)]

    #kinda ugly but it works
    for col in range(8):
        if col == 0:
            distList[7][col][getIndex("rook1")] = 1
            distList[6][col][getIndex("pawn1")] = 1
        elif col == 1:
            distList[7][col][getIndex("knight1")] = 1
            distList[6][col][getIndex("pawn2")] = 1
        elif col == 2:
            distList[7][col][getIndex("bishop1")] = 1
            distList[6][col][getIndex("pawn3")] = 1
        elif col == 3:
            distList[7][col][getIndex("queen")] = 1
            distList[6][col][getIndex("pawn4")] = 1
        elif col == 4:
            distList[7][col][getIndex("king")] = 1
            distList[6][col][getIndex("pawn5")] = 1
        elif col == 5:
            distList[7][col][getIndex("bishop2")] = 1
            distList[6][col][getIndex("pawn6")] = 1
        elif col == 6:
            distList[7][col][getIndex("knight2")] = 1
            distList[6][col][getIndex("pawn7")] = 1
        elif col == 7:
            distList[7][col][getIndex("rook2")] = 1
            distList[6][col][getIndex("pawn8")] = 1
    
    return distList

def printDist(distList):

    for row in range (7, -1, -1):
        for col in range(0, 8):
            print("|_|", end = " ")
            print(distList[row][col])
        print()

class p5v2(Player):
    def handle_game_start(self, color: Color, board: chess.Board):
        distList = initDist()
        self.board = board
        self.color = color
        
    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):
        pass

    def choose_sense(self, sense_actions: List[Square], move_actions: List[chess.Move], seconds_left: float) -> Square:
        return random.choice(sense_actions)

    def handle_sense_result(self, sense_result: List[Tuple[Square, Optional[chess.Piece]]]):
        pass

    def choose_move(self, move_actions: List[chess.Move], seconds_left: float) -> Optional[chess.Move]:
        return random.choice(move_actions + [None])

    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move],
                           captured_opponent_piece: bool, capture_square: Optional[Square]):
        pass

    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason],
                        game_history: GameHistory):
        pass
