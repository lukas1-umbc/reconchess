import random
from reconchess import *

# The goal of this bot is to have a semi-rigid opener. Specifically, it will attempt a 5-move checkmate
# while sensing potential problems and countering them.
# If stopped, the bot will default to random moves.

# Sequences are in reverse order, so that adding moves in order to recover and popping moves is efficient.
# Moves are not flipped like in AttackBot because black and white behave slightly differently.
move_list = [
    # White initial checkmate setup
    [chess.Move(chess.G5, chess.F7), # Knight capture King
     chess.Move(chess.F7, chess.F8), # Queen capture King (pop if queen captured)
     chess.Move(chess.H5, chess.F8), # Queen capture Pawn or King (Could be blocked)
     chess.Move(chess.H3, chess.G5), # Knight moving to position (Could be captured by Queen; set QH5>G5)
     chess.Move(chess.D1, chess.H5), # Queen moving to position (Account for captures here) Go to F3 if qH4 or kF6
     chess.Move(chess.G3, chess.H3), # Knight releases from home
     chess.Move(chess.E2, chess.E3)  # King's Pawn releases (Counters 4-move w/ bishop)
    ],
    
    # Black initial checkmate setup
    [chess.Move(chess.G4, chess.F2), # Knight capture King
     chess.Move(chess.F2, chess.E1), # Queen capture King (pop if queen captured)
     chess.Move(chess.H4, chess.E1), # Queen captures Pawn or ends (Could be blocked)
     chess.Move(chess.H6, chess.G4), # Knight moving to position 
     chess.Move(chess.G8, chess.F6), # Knight releases from home (Checks for knight on F6)
     chess.Move(chess.D8, chess.H4), # Queen moving to position (Account for captures here)
     chess.Move(chess.E7, chess.E6)  # King's Pawn releases (Counters 4-move w/ bishop)
    ]
]

# The scans performed here are to check for threats that moves alone can not cover
# Again, the list is in reverse order such that the first scan is the last listed
scan_list = [
    # White initial scan order
    [chess.E7, # Check King's position
     chess.F7, # Anything at G6, check King's position
     chess.E4, # Knight rushes; capture knights if possible or proceed w/ rescan (kE5)
     chess.D5, # Conditional scanning: If King's Pawn or King's Knight, G5. Else D5. Change Queen move here
     chess.F7, # King's Knight, King's Pawn, and Pawn at G6
     chess.E7  # Black hasn't moved yet
    ],
    # Black initial scan order
    [chess.E2  # Check King's position
     chess.F2  # Anything at G6, check King's position
     chess.G4  # Check for 5-move checkmate and Queen safety (take piece in H5)
     chess.D5, # Knight rushes, F6 covered by knight move (May have to pC7 > C6)
     chess.G4, # Could make conditional... Verifies Queen safety 
     chess.F2  # King's Knight, King's Pawn, and Pawn at G3
    ]
]

turn_number = 0
WHITE = 0
BLACK = 1
list_choice = None
class OpenerOnly(Player):
    def __init__(self):
        pass

    def handle_game_start(self, color: Color, board: chess.Board):
        self.color = color
        self.board = board
        
        if color == chess.BLACK:
            list_choice = BLACK
        else:
            list_choice = WHITE

    # This function can't determine what move to take, so latest_captured holds the move instead
    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):
        # store where capture happened for decision making later
        self.latest_captured = capture_square
        # remove captured pieces
        if captured_my_piece:
            self.board.remove_piece_at(capture_square)

    def choose_sense(self, sense_actions: List[Square], move_actions: List[chess.Move], seconds_left: float) -> Square:
        turn_number = turn_number + 1 # done when sensing to keep turn number consistent when referencing arrays

        if len(self.scan_list) == 0:
            # An algorithm to generate scans would go here
            return random.choice(sense_actions + [None]) #could be bound to between G2 and B7
        else:
            return self.scan_list[list_choice].pop()

    # This function can't determine what move to take
    def handle_sense_result(self, sense_result: List[Tuple[Square, Optional[chess.Piece]]]):
        # dumb adding of pieces, doesn't try to predict and remove previous pieces from the board
        for square, piece in sense_result:
            self.board.set_piece_at(square, piece)

    def choose_move(self, move_actions: List[chess.Move], seconds_left: float) -> Optional[chess.Move]:
        # A simple capture if capturable script will be inserted here, which will handle random rushes
        # Also, the opener needs to be aborted if one of the key pieces was captured
        while len(self.move_list[list_choice]) > 0 and self.move_list[list_choice][-1] not in move_actions:
            self.move_list[list_choice].pop()
        # Most likely abort the opener if this loop triggers during it

        if len(self.move_list[list_choice]) == 0:
            # An algorithm to generate moves would go here
            return random.choice(move_actions + [None])
        else:
            return self.move_sequence.pop(0)

    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move],
                           captured_opponent_piece: bool, capture_square: Optional[Square]):
        # transfer result to the internal board
        if taken_Move is not None:
            self.board.push(taken_move)

    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason],
                        game_history: GameHistory):
        pass
