import random
import pprint
from reconchess import *

# 8x8x16 list
distList = [[ [0 for dist in range(6)] for row in range(8)] for col in range(8)]
# number of pieces the opponent has left
oppPiecesLeft = 16

# Dictionary to make it easy to index with the probability distributions.
# e.g. getIndex("king") will return the king's index in a given square's probability distribution list.
# These indexes are based on those used by pychess
# https://imgur.com/a/zRJgRnf - note: no longer accurate, but the spirit of the design is still there
def getIndex(pieceName):
    pieceIndexer = {
        "pawn": 0, "knight": 1, "bishop": 2, "rook": 3, "queen": 4, "king": 5
    }
    return pieceIndexer[pieceName]

# initializes the 3D list we use to keep the probability distributions of each square
def initDist():

    # kinda ugly but it works
    for col in range(8):
        if col == 0:
            distList[7][col][getIndex("rook")] = 1
            distList[6][col][getIndex("pawn")] = 1
        elif col == 1:
            distList[7][col][getIndex("knight")] = 1
            distList[6][col][getIndex("pawn")] = 1
        elif col == 2:
            distList[7][col][getIndex("bishop")] = 1
            distList[6][col][getIndex("pawn")] = 1
        elif col == 3:
            distList[7][col][getIndex("queen")] = 1
            distList[6][col][getIndex("pawn")] = 1
        elif col == 4:
            distList[7][col][getIndex("king")] = 1
            distList[6][col][getIndex("pawn")] = 1
        elif col == 5:
            distList[7][col][getIndex("bishop")] = 1
            distList[6][col][getIndex("pawn")] = 1
        elif col == 6:
            distList[7][col][getIndex("knight")] = 1
            distList[6][col][getIndex("pawn")] = 1
        elif col == 7:
            distList[7][col][getIndex("rook")] = 1
            distList[6][col][getIndex("pawn")] = 1
    
    return distList

# goes row by row and prints out each square's distribution - for testing
def printDist(distList):

    for row in range (7, -1, -1):
        for col in range(0, 8):
            print("|", row, ", ", col, "|", end = " ")
            print(distList[row][col])
        print()

class p5v2(Player):
    def handle_game_start(self, color: Color, board: chess.Board):
        distList = initDist()
        #printDist(distList)
        self.board = board
        self.color = color
        
    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):
        pass

    def choose_sense(self, sense_actions: List[Square], move_actions: List[chess.Move], seconds_left: float) -> Square:
        return random.choice(sense_actions)

    # Board estimate updates should go here
    def handle_sense_result(self, sense_result: List[Tuple[Square, Optional[chess.Piece]]]):       
        # add the pieces in the sense result to our board
        # also want to change probabilities for those spaces to 1 for the appropriate pieces
        # square is an int between 0 and 63; count from the bottom to bottom top, left to right
        # for piece, uppercase is white, lowercase is black
        for square, piece in sense_result:           

            row = square//8
            col = square - (row * 8)
            
            # if the square has a piece
            if piece is not None:
                # pawn
                global distList
                if piece.piece_type == 1:
                    distList[row][col][getIndex("pawn")] = 1
                # knight
                elif piece.piece_type == 2:
                    distList[row][col][getIndex("knight")] = 1
                # bishop
                elif piece.piece_type == 3:
                    distList[row][col][getIndex("bishop")] = 1
                # rook
                elif piece.piece_type == 4:
                    distList[row][col][getIndex("rook")] = 1
                # queen
                elif piece.piece_type == 5:
                    distList[row][col][getIndex("queen")] = 1
                # king
                elif piece.piece_type == 6:
                    distList[row][col][getIndex("king")] = 1

            self.board.set_piece_at(square, piece)
        

    def choose_move(self, move_actions: List[chess.Move], seconds_left: float) -> Optional[chess.Move]:
        return random.choice(move_actions + [None])

    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move],
                           captured_opponent_piece: bool, capture_square: Optional[Square]):
        # if we captured a piece, decrement opponent's piece count
        if captured_opponent_piece:
            global oppPiecesLeft
            oppPiecesLeft -= 1

        # if a move was executed, apply it to our board
        if taken_move is not None:
            self.board.push(taken_move)

    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason],
                        game_history: GameHistory):
        printDist(distList)
        pass
