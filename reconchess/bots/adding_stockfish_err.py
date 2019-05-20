import random
import pprint
import numpy
from reconchess import *
import chess.engine
import os
import sys

STOCKFISH_ENV_VAR = 'STOCKFISH_EXECUTABLE'

numBadStates = 0

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
            total = 0;
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

    #initializing Stockfish
    def __init__(self):
        self.board = None
        self.color = None
        self.my_piece_captured_square = None

        # make sure stockfish environment variable exists
        if STOCKFISH_ENV_VAR not in os.environ:
            raise KeyError(
                'TroutBot requires an environment variable called "{}" pointing to the Stockfish executable'.format(
                    STOCKFISH_ENV_VAR))

        # make sure there is actually a file
        stockfish_path = os.environ[STOCKFISH_ENV_VAR]
        if not os.path.exists(stockfish_path):
            raise ValueError('No stockfish executable found at "{}"'.format(stockfish_path))

        # initialize the stockfish engine
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

    def handle_game_start(self, color: Color, board: chess.Board):
        distList = initDist(color)
        #printDist(distList)
        self.board = board
        self.color = color
        print(self.color)

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):

        # if the opponent captured our piece, remove it from our board.
        self.my_piece_captured_square = capture_square
        if captured_my_piece:
            self.board.remove_piece_at(capture_square)


    def choose_sense(self, sense_actions: List[Square], move_actions: List[chess.Move], seconds_left: float) -> Square:

        # if our piece was just captured, sense where it was captured
        if self.my_piece_captured_square:
            return self.my_piece_captured_square

        # if we might capture a piece when we move, sense where the capture will occur
        future_move = self.choose_move(move_actions, seconds_left)
        if future_move is not None and self.board.piece_at(future_move.to_square) is not None:
            return future_move.to_square

        getSingleTotals()
        get9SquareTotals()
        max_row = 0;
        max_col = 0;
        max_tot = 0;
        #find largest sum of 9 squares
        for row in range(8):
            for col in range(8):
                if dist9SquareTots[row][col] > max_tot:
                    max_tot = dist9SquareTots[row][col]
                    max_col = col;
                    max_row = row;

        #get number of board square 0-63 that sensing square will be centered on
        sensing_index = max_row*8 + max_col

        return sense_actions[sensing_index]


    # Board estimate updates should go here
    def handle_sense_result(self, sense_result: List[Tuple[Square, Optional[chess.Piece]]]):

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
        #printDist(distList)



    def choose_move(self, move_actions: List[chess.Move], seconds_left: float) -> Optional[chess.Move]:

        # if we might be able to take the king, try to (copied from trout_bot.py)
        enemy_king_square = self.board.king(not self.color)
        if enemy_king_square:
            # if there are any ally pieces that can take king, execute one of those moves
            enemy_king_attackers = self.board.attackers(self.color, enemy_king_square)
            if enemy_king_attackers:
                attacker_square = enemy_king_attackers.pop()
                return chess.Move(attacker_square, enemy_king_square)

        # clear the board of all pieces and re-add our own pieces
        # this was the only way to do it
        #tempBoard = chess.Board(self.board.fen())

        #for curr_index in range(64):
            #piece = tempBoard.remove_piece_at(curr_index)
            #if piece != None and piece.color == self.color:
              # tempBoard.set_piece_at(curr_index, piece)

        # loop through the probabilities and add opponent piece if the probability is high enough
        num_pawns = 0
        # default king is at starting position
        # we are the white player
        if self.color == True:
            king_index = 60
        # we are the black player
        else:
            king_index = 4
        king_prob = 0

        for row in range(8):
            for col in range(8):

                # number 0-63 of the square
                curr_index = row*8 + col

                max_prob = 0
                max_type = 0

                # which piece has a higher probability of being in the square
                for piece_type in range(6):

                    # we will take the highest probability for location of the king and add it at the end
                    if piece_type == getIndex("king"):
                        if distList[row][col][piece_type] > king_prob:
                            king_prob = distList[row][col][piece_type]
                            king_index = curr_index

                    # out of the remaining piece types, which has the highest probability
                    elif distList[row][col][piece_type] > max_prob:
                        max_prob = distList[row][col][piece_type]
                        max_type = piece_type

                # if the probability of the piece being in the square is high, add an opponent piece to the board
                if max_prob >= .75:

                    # max of 8 pawns
                    if max_type == getIndex("pawn"):
                        if num_pawns < 8:
                            self.board.set_piece_at(curr_index, chess.Piece(getIndex("pawn") + 1, not self.color))
                            num_pawns = num_pawns + 1

                    # other pieces
                    else:
                        self.board.set_piece_at(curr_index, chess.Piece(max_type + 1, not self.color))

        # add the king wherever the highest probability is
        self.board.set_piece_at(king_index, chess.Piece(getIndex("king") + 1, not self.color))

        # if we might be able to take the king, try to (copied from trout_bot.py)
        enemy_king_square = self.board.king(not self.color)
        if enemy_king_square:
            # if there are any ally pieces that can take king, execute one of those moves
            enemy_king_attackers = self.board.attackers(self.color, enemy_king_square)
            if enemy_king_attackers:
                attacker_square = enemy_king_attackers.pop()
                return chess.Move(attacker_square, enemy_king_square)

        print()
        print("self.board: ")
        print(self.board)
        #print("tempBoard: ")
       # print(tempBoard)
        #printDist(distList)  

        # testing - check whether the board we feed to stockfish has our king
        foundKing = False
        for i in range(0, 64):
            kingPiece = self.board.piece_at(i)
            if kingPiece is not None and kingPiece.piece_type == 6 and kingPiece.color is self.color:
                foundKing = True
        if foundKing == False:
            print("Couldn't find our king, exiting.")
            sys.exit()

        #Stockfish: copied from TroutBot
        try:
            self.board.turn = self.color
            self.board.clear_stack()
            result = self.engine.play(self.board, chess.engine.Limit(time=0.5))
            if result.move in move_actions:
                return result.move
        except (chess.engine.EngineError, chess.engine.EngineTerminatedError) as e:
            print('Engine bad state at "{}"'.format(self.board.fen()))
            print(e)
            global numBadStates
            numBadStates+=1

        # if stockfish fails
        move = random.choice(move_actions + [None])
        while move not in move_actions:
                return random.choice(move_actions + [None])
        return move



    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move],
                           captured_opponent_piece: bool, capture_square: Optional[Square]):
        global distList
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

    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason],
                        game_history: GameHistory):
        print("Number of bad states = ", numBadStates)
        self.engine.quit()
