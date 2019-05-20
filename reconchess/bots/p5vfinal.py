import random
import pprint
import numpy
from reconchess import *
import chess.engine
import os
import sys

# Sequences are in reverse order, so that adding moves in order to recover and popping moves is efficient.
# Moves are not flipped like in AttackBot because black and white behave slightly differently.
OPEN_MOVES = [
    # White initial checkmate setup
    [# The capturing of the king should happen incidentally
     chess.Move(chess.F3, chess.F7), # Queen captures Pawn
     chess.Move(chess.H5, chess.F8), # Queen capture Pawn or King (Could be blocked)
     chess.Move(chess.H3, chess.G5), # Knight moving to position (Could be captured by Queen; set QH5>G5)
     chess.Move(chess.D1, chess.H5), # Queen moving to position (Account for captures here) Go to F3 if G3 or kF6
     chess.Move(chess.G3, chess.H3), # Knight releases from home
     chess.Move(chess.E2, chess.E3), # King's Pawn releases (Counters 4-move w/ bishop)
    ],

    # Black initial checkmate setup
    [# The capturing of the king should happen incidentally
     chess.Move(chess.F6, chess.F2), # Queen captures Pawn
     chess.Move(chess.H4, chess.E1), # Queen captures Pawn or ends (Could be blocked)
     chess.Move(chess.F6, chess.G4), # Knight moving to position
     chess.Move(chess.G8, chess.F6), # Knight releases from home (Checks for knight on F6)
     chess.Move(chess.D8, chess.H4), # Queen moving to position (Account for captures here)
     chess.Move(chess.E7, chess.E6), # King's Pawn releases (Counters 4-move w/ bishop)
    ]
]

# The scans performed here are to check for threats that moves alone can not cover
# Again, the list is in reverse order such that the first scan is the last listed
OPEN_SCANS = [
    # White initial scan order
    [chess.E7, # Check King's position
     chess.F7, # Anything at G6, check King's position
     chess.E4, # Knight rushes; capture knights if possible or proceed w/ rescan (kE5)
     chess.D5, # Conditional scanning: If King's Pawn or King's Knight, G5. Else D5. Change Queen move here
     chess.F7, # King's Knight, King's Pawn, and Pawn at G6
     chess.E7, # Black hasn't moved yet
    ],
    # Black initial scan order
    [chess.E2, # Check King's position
     chess.F2, # Anything at G6, check King's position
     chess.G4, # Check for 5-move checkmate and Queen safety (take piece in H5)
     chess.D5, # Knight rushes, F6 covered by knight move (May have to pC7 > C6)
     chess.G4, # Could make conditional... Verifies Queen safety
     chess.F2, # King's Knight, King's Pawn, and Pawn at G3
    ]
]

# 8x8x16 list
distList = [[ [0 for dist in range(6)] for row in range(8)] for col in range(8)]
# number of pieces the opponent has left
oppPiecesLeft = 16

# sums of the probabilities of all pieces on a square
distSingleTots = [[ 0 for row in range(8)] for col in range(8)]

# sums of the probabilities of the 3x3 squares
# for index [row][col] the value is the sum of the 3x3 square centered at [row][col]
dist9SquareTots = [[ 0 for row in range(8)] for col in range(8)]

# populate distSingleTots by adding up probabilities of all pieces for a square
def getSingleTotals():
    for row in range(8):
        for col in range(8):
            total = 0;
            for dist in range(6):
                total += distList[row][col][dist]
            distSingleTots[row][col] = total

# populate dist9SquareTots using single square totals
def get9SquareTotals():

    # exclude row and col 0 and 7 because we dont want to center on a side square
    for row in range(1,7):
        for col in range(1,7):
            total = 0
            total += distSingleTots[row-1][col-1]
            total += distSingleTots[row-1][col]
            total += distSingleTots[row-1][col+1]
            total += distSingleTots[row][col-1]
            total += distSingleTots[row][col]
            total += distSingleTots[row][col+1]
            total += distSingleTots[row+1][col-1]
            total += distSingleTots[row+1][col]
            total += distSingleTots[row+1][col+1]
            dist9SquareTots[row][col] = total

# Dictionary to make it easy to index with the probability distributions.
# e.g. getIndex("king") will return the king's index in a given square's probability distribution list.
# These indexes are based on those used by pychess
# https://imgur.com/a/zRJgRnf - note: no longer accurate, but the spirit of the design is still there
def getIndex(pieceName):
    pieceIndexer = {
        "pawn": 0, "knight": 1, "bishop": 2, "rook": 3, "queen": 4, "king": 5
    }
    return pieceIndexer[pieceName]

def tupSub(tup1, tup2):
    return tuple(abs(numpy.subtract(tup1, tup2)))

# initializes the 3D list we use to keep the probability distributions of each square
def initDist(color):

    # if we are white player
    if (color):
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

    # if we are black player
    else:
            for col in range(8):
                if col == 0:
                    distList[0][col][getIndex("rook")] = 1
                    distList[1][col][getIndex("pawn")] = 1
                elif col == 1:
                    distList[0][col][getIndex("knight")] = 1
                    distList[1][col][getIndex("pawn")] = 1
                elif col == 2:
                    distList[0][col][getIndex("bishop")] = 1
                    distList[1][col][getIndex("pawn")] = 1
                elif col == 3:
                    distList[0][col][getIndex("queen")] = 1
                    distList[1][col][getIndex("pawn")] = 1
                elif col == 4:
                    distList[0][col][getIndex("king")] = 1
                    distList[1][col][getIndex("pawn")] = 1
                elif col == 5:
                    distList[0][col][getIndex("bishop")] = 1
                    distList[1][col][getIndex("pawn")] = 1
                elif col == 6:
                    distList[0][col][getIndex("knight")] = 1
                    distList[1][col][getIndex("pawn")] = 1
                elif col == 7:
                    distList[0][col][getIndex("rook")] = 1
                    distList[1][col][getIndex("pawn")] = 1

    return distList

# goes row by row and prints out each square's distribution - for testing
def printDist(distList):

    for row in range (7, -1, -1):
        for col in range(0, 8):
            print("|", row, ", ", col, "|", end = " ")
            print(distList[row][col])
        print()

class p5v4(Player):

    def __init__(self):
        self.board = None
        self.color = None
        self.latest_captured = None
        self.turn_number = int

    def handle_game_start(self, color: Color, board: chess.Board):
        distList = initDist(color)
        #printDist(distList)
        self.color = color
        self.board = board
        self.turn_number = 0

        self.my_piece_captured_square = None
        self.selected_move = None
        self.strength = 0

        if self.color == chess.BLACK:
            self.move_list = OPEN_MOVES[1]
            self.scan_list = OPEN_SCANS[1]
        else:
            self.move_list = OPEN_MOVES[0]
            self.scan_list = OPEN_SCANS[0]

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):

        # store where capture happened for decision making later
        self.latest_captured = capture_square
        # abort remaining moves if queen is captured
        if captured_my_piece and self.board.piece_at(capture_square) is chess.QUEEN:
            self.move_list.clear()
            self.scan_list.clear()
            self.scan_list.append(capture_square)

        # remove captured pieces
        self.my_piece_captured_square = capture_square
        if captured_my_piece:
            self.board.remove_piece_at(capture_square)


    def choose_sense(self, sense_actions: List[Square], move_actions: List[chess.Move], seconds_left: float) -> Square:

        self.turn_number = self.turn_number + 1 # done when sensing to keep turn number consistent when referencing arrays

        # if our piece was just captured, sense where it was captured
        if self.my_piece_captured_square:
            return self.my_piece_captured_square

        # if we might capture a piece when we move, sense where the capture will occur
        future_move = self.choose_move(move_actions, seconds_left)
        if future_move is not None and self.board.piece_at(future_move.to_square) is not None:
            return future_move.to_square

        if len(self.scan_list) == 0:
            getSingleTotals()
            get9SquareTotals()
            max_row = 0
            max_col = 0
            max_tot = 0
            #find largest sum of 9 squares
            for row in range(8):
                for col in range(8):
                    if dist9SquareTots[row][col] > max_tot:
                        max_tot = dist9SquareTots[row][col]
                        max_col = col
                        max_row = row
            #get number of board square 0-63 that sensing square will be centered on
            sensing_index = max_row*8 + max_col
            return sense_actions[sensing_index]
        else:
            return self.scan_list.pop()


    # Board estimate updates should go here
    def handle_sense_result(self, sense_result: List[Tuple[Square, Optional[chess.Piece]]]):

        # Relies on the skipping impossible moves function to make sure the queen gets to the new position
        if self.turn_number < 8:
            if self.color == chess.BLACK and (self.board.piece_at(chess.G3) is not None or self.board.piece_at(chess.F3) is chess.KNIGHT):
                if self.board.piece_at(chess.F3) is None and self.board.piece_at(chess.F4) is None:
                    self.move_list.append(chess.Move(chess.D8, chess.F6))
                    self.move_list.append(chess.Move(chess.H4, chess.F6))
                    self.move_list.append(chess.Move(chess.G5, chess.F6))
                else:
                    self.move_list.clear()
                    self.scan_list.clear()
                    self.move_list.append(chess.Move(chess.G8, chess.H6))
                    self.move_list.append(chess.Move(chess.F8, chess.E7))
                    self.move_list.append(chess.Move(chess.E8, chess.G8))
            if self.color == chess.WHITE and (self.board.piece_at(chess.G6) is not None or self.board.piece_at(chess.F6) is chess.KNIGHT):
                if self.board.piece_at(chess.F3) is None and self.board.piece_at(chess.F4) is None:
                    self.move_list.append(chess.Move(chess.D1, chess.F3))
                    self.move_list.append(chess.Move(chess.H5, chess.F3))
                    self.move_list.append(chess.Move(chess.G4, chess.F3))
                else:
                    self.move_list.clear()
                    self.scan_list.clear()
                    self.move_list.append(chess.Move(chess.G1, chess.H3))
                    self.move_list.append(chess.Move(chess.F1, chess.E2))
                    self.move_list.append(chess.Move(chess.E1, chess.G1))

        global distList

        # rough estimate of the number of possible moves for an opponent's piece
        # from my research, 30 seems like a common average number of possible moves in a turn for a player
        n = 30/oppPiecesLeft

        # add the pieces in the sense result to our board
        # also want to change probabilities for those spaces to 1 for the appropriate pieces
        # square is an int between 0 and 63; count from the bottom to bottom top, left to right
        # for piece, uppercase is white, lowercase is black
        # true = white, false = black
        for square, piece in sense_result:

            row = square//8
            col = square - (row * 8)
            pieceList = []

            # if the square has a piece
            if piece is not None and piece.color != self.color:

                pieceIndex = piece.piece_type - 1

                # update the distributions for each square with a piece in the sense
                distList[row][col][pieceIndex] = 1
                for i in range(0, 6):
                    if i != pieceIndex:
                        distList[row][col][i] = 0

                # find the squares on the board whose highest probabilites in their distributions are the current piece in the current square
                for i in range(7, -1, -1):
                    for j in range(0, 8):
                        if distList[i][j].index(max(distList[i][j])) == pieceIndex:
                            pieceList.append((i, j))

                # find the square in pieceList closest to the current square (This was really hard to do)
                magicTup = min(pieceList, key = lambda x: tupSub(x, (row, col)))

                # adjust that square's probability for the current piece (MOVE)
                stayProb = distList[magicTup[0]][magicTup[1]][pieceIndex] * ((oppPiecesLeft-1)/oppPiecesLeft)
                distList[magicTup[0]][magicTup[1]][pieceIndex] = distList[magicTup[0]][magicTup[1]][pieceIndex] + ((1-stayProb)/n)
                pieceList.remove(magicTup)

                # adjust the rest of the square's probabilities (STAY)
                for pair in pieceList:
                    distList[pair[0]][pair[1]][pieceIndex] *= ((oppPiecesLeft-1)/oppPiecesLeft)

            # square has piece but its ours - might not even be necessary but can't hurt
            elif piece is not None and piece.color == self.color:
                for i in range(0, 6):
                    distList[row][col][i] = 0

            # square has no piece
            elif piece is None:
                # update the distributions for each square with no piece
                # no piece, so set all probabilities in distribution to 0
                for i in range(0,6):
                    distList[row][col][i] = 0

            self.board.set_piece_at(square, piece)


    def choose_move(self, move_actions: List[chess.Move], seconds_left: float) -> Optional[chess.Move]:

        if self.latest_captured:
            # if there are any ally pieces that can take revenge
            revenge_attackers = self.board.attackers(self.color, self.latest_captured)
            if revenge_attackers:
                attacker_square = revenge_attackers.pop()
                self.move_list.append(chess.Move(attacker_square, self.latest_captured))

        if self.turn_number < 6:
            # Check for knight attempting to rush king
            if self.color == chess.BLACK:
                knight_check = chess.D6
            else:
                knight_check = chess.D3
            if self.board.piece_at(knight_check) is not None:
                knight_attackers = self.board.attackers(self.color, knight_check)
                if knight_attackers:
                    attacker_square = knight_attackers.pop()
                    self.move_list.append(chess.Move(attacker_square, knight_check))

        # if we might be able to take the king, try to (copied from trout_bot.py)
        enemy_king_square = self.board.king(not self.color)
        if enemy_king_square:
            # if there are any ally pieces that can take king, execute one of those moves
            enemy_king_attackers = self.board.attackers(self.color, enemy_king_square)
            if enemy_king_attackers:
                attacker_square = enemy_king_attackers.pop()
                if chess.Move(attacker_square, enemy_king_square) in move_actions:
                    return chess.Move(attacker_square, enemy_king_square)

        # Removes impossible moves
        while len(self.move_list) > 0 and self.move_list[-1] not in move_actions:
            self.move_list.pop()

        if len(self.move_list) == 0:
            # BRANDI: MOVE GENERATION ALGORITHM GOES HERE, IN PLACE OF THE RANDOM SELECTION

            self.selected_move = None

            for move in move_actions:
                if self.board.piece_at(move.to_square) is chess.KING:
                    self.selected_move = move
                    return self.selected_move
                elif self.board.piece_at(move.to_square) is chess.QUEEN:
                    self.selected_move = move
                    return self.selected_move
                else:
                    if self.board.piece_at(move.to_square) is chess.PAWN:
                        if self.strength < 1:
                            self.strength = 1
                            self.selected_move = move
                    elif self.board.piece_at(move.to_square) is chess.BISHOP:
                        if self.strength < 3:
                            self.strength = 3
                            self.selected_move = move
                    elif self.board.piece_at(move.to_square) is chess.KNIGHT:
                        if self.strength < 7:
                            self.strength = 7
                            self.selected_move = move
                    elif self.board.piece_at(move.to_square) is chess.ROOK:
                        if self.strength < 5:
                            self.strength = 5
                            self.selected_move = move
                    else:
                        self.selected_move = random.choice(move_actions + [None])

            return self.selected_move

            #return random.choice(move_actions + [None])
        else:
            return self.move_list.pop()




    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move],
                           captured_opponent_piece: bool, capture_square: Optional[Square]):

        global distList
        # Used to push the queen to her intended destination
        if self.turn_number < 8 and requested_move != taken_move:
            if self.board.piece_at(requested_move.from_square) == chess.QUEEN:
                self.move_list.append(chess.Move(taken_move.to_square, requested_move.to_square))

        # if we captured a piece, decrement opponent's piece count
        # we also want to set all the probabilities of this square to 0
        if captured_opponent_piece:
            global oppPiecesLeft
            oppPiecesLeft -= 1
            row = capture_square//8
            col = capture_square - (row * 8)
            for prob in range(0, 6):
                distList[row][col][prob] = 0

        # if a move was executed, apply it to our board
        # we also want to set all probabilities in the square we moved to to 0
        if taken_move is not None:
            self.board.push(taken_move)
            square = taken_move.to_square
            row = square//8
            col = square - (row * 8)
            for prob in range(0, 6):
                distList[row][col][prob] = 0

        # Reset latest_capture now that its been used
        if self.latest_captured:
            self.latest_captured = None

    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason],
                        game_history: GameHistory):
        pass
