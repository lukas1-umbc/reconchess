import random
from reconchess import *

# The goal of this bot is to have a semi-rigid opener. Specifically, it will attempt a 5-move checkmate
# while sensing potential problems and countering them.
# If stopped, the bot will default to random moves.

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

class OpenerOnly(Player):
    def __init__(self):
        self.board = None
        self.color = None
        self.latest_captured = None
        self.turn_number = int

    def handle_game_start(self, color: Color, board: chess.Board):
        self.color = color
        self.board = board
        self.turn_number = 0;
        
        if self.color == chess.BLACK:
            self.move_list = OPEN_MOVES[1]
            self.scan_list = OPEN_SCANS[1]
        else:
            self.move_list = OPEN_MOVES[0]
            self.scan_list = OPEN_SCANS[0]

    # This function can't determine what move to take, so latest_captured holds the move instead
    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):
        # store where capture happened for decision making later
        self.latest_captured = capture_square
        # abort remaining moves if queen is captured
        if captured_my_piece and self.board.piece_at(capture_square) is chess.QUEEN:
            move_list.clear()
            scan_list.clear()
            scan_list.append(capture_square)
        
        # remove captured pieces
        if captured_my_piece:
            self.board.remove_piece_at(capture_square)

    def choose_sense(self, sense_actions: List[Square], move_actions: List[chess.Move], seconds_left: float) -> Square:
        self.turn_number = self.turn_number + 1 # done when sensing to keep turn number consistent when referencing arrays

        if len(self.scan_list) == 0:
            # An algorithm to generate scans would go here
            return random.choice(sense_actions) #could be bound to between G2 and B7
        else:
            return self.scan_list.pop()

    # This function can't determine what move to take
    def handle_sense_result(self, sense_result: List[Tuple[Square, Optional[chess.Piece]]]):
        # dumb adding of pieces, doesn't try to predict and remove previous pieces from the board
        for square, piece in sense_result:
            self.board.set_piece_at(square, piece)

        # Relies on the skipping impossible moves function to make sure the queen gets to the new position
        if self.turn_number < 8:
            if self.color == chess.BLACK and (self.board.piece_at(chess.G3) is not None or self.board.piece_at(chess.F3) is chess.KNIGHT):
                if self.board.piece_at(chess.F3) is None and self.board.piece_at(chess.F4) is None:
                    self.move_list.append(chess.Move(chess.D8, chess.F6))
                    self.move_list.append(chess.Move(chess.H4, chess.F6))
                    self.move_list.append(chess.Move(chess.G5, chess.F6))
                else:
                    move_list.clear()
                    scan_list.clear()
                    self.move_list.append(chess.Move(chess.G8, chess.H6))
                    self.move_list.append(chess.Move(chess.F8, chess.E7))
                    self.move_list.append(chess.Move(chess.E8, chess.G8))
            if self.color == chess.WHITE and (self.board.piece_at(chess.G6) is not None or self.board.piece_at(chess.F6) is chess.KNIGHT):
                if self.board.piece_at(chess.F3) is None and self.board.piece_at(chess.F4) is None:
                    self.move_list.append(chess.Move(chess.D1, chess.F3))
                    self.move_list.append(chess.Move(chess.H5, chess.F3))
                    self.move_list.append(chess.Move(chess.G4, chess.F3))
                else:
                    move_list.clear()
                    scan_list.clear()
                    self.move_list.append(chess.Move(chess.G1, chess.H3))
                    self.move_list.append(chess.Move(chess.F1, chess.E2))
                    self.move_list.append(chess.Move(chess.E1, chess.G1))
                    
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

        # Always default to attempting to capture king if possible
        enemy_king_square = self.board.king(not self.color)
        if enemy_king_square:
            # if there are any ally pieces that can take king, execute one of those moves
            enemy_king_attackers = self.board.attackers(self.color, enemy_king_square)
            if enemy_king_attackers:
                attacker_square = enemy_king_attackers.pop()
                self.move_list.append(chess.Move(attacker_square, enemy_king_square))

        # Removes impossible moves
        while len(self.move_list) > 0 and self.move_list[-1] not in move_actions:
            self.move_list.pop()

        if len(self.move_list) == 0:
            # An algorithm to generate moves would go here
            return random.choice(move_actions + [None])
        else:
            return self.move_list.pop()

    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move],
                           captured_opponent_piece: bool, capture_square: Optional[Square]):
        # Used to push the queen to her intended destination
        if self.turn_number < 8 and requested_move != taken_move:
            if self.board.piece_at(requested_move.from_square) == chess.QUEEN:
                self.move_list.append(chess.Move(taken_move.to_square, requested_move.to_square))

        # Reset latest_capture now that its been used
        if self.latest_captured:
            self.latest_captured = None
        
        # transfer result to the internal board
        if taken_move is not None:
            self.board.push(taken_move)

    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason],
                        game_history: GameHistory):
        pass
