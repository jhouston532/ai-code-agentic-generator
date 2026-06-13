# Constants and Imports

PIECE_TYPES = {
    'p': 'Pawn',
    'n': 'Knight',
    'b': 'Bishop',
    'r': 'Rook',
    'q': 'Queen',
    'k': 'King'
}

MOVE_NOTATION = {
    'move': '{}{}-{}{}'.format,
    'capture': '{}{}x{}{}'.format
}

FILE_NAME = "chess_game.txt"

import pygame

class Piece:
    def __init__(self, piece_type):
        self.piece_type = piece_type
        self.is_white = True if piece_type.isupper() else False
        self.symbol = piece_type.lower() if self.is_white else piece_type.upper()

    def __str__(self):
        return self.symbol

class ChessBoard:
    FILE_NAME = "chess_moves.txt"

    def __init__(self):
        self.board = [['' for _ in range(8)] for _ in range(8)]
        self.initialize_board()
        self.current_player = "White"

    def initialize_board(self):
        pieces = {
            'r': Piece('Rook'),
            'n': Piece('Knight'),
            'b': Piece('Bishop'),
            'q': Piece('Queen'),
            'k': Piece('King'),
            'p': Piece('Pawn')
        }

        for i in range(8):
            self.board[1][i] = pieces['p']
            self.board[6][i] = pieces['P']

        piece_rows = {
            0: [pieces['r'], pieces['n'], pieces['b'], pieces['q'], pieces['k'], pieces['b'], pieces['n'], pieces['r']],
            7: [pieces['R'], pieces['N'], pieces['B'], pieces['Q'], pieces['K'], pieces['B'], pieces['N'], pieces['R']]
        }

        for row, pieces_row in piece_rows.items():
            for col, piece in enumerate(pieces_row):
                self.board[row][col] = piece

    def move_piece(self, start, end):
        piece = self.board[start[0]][start[1]]
        if isinstance(piece, Piece) and (piece.is_white == True or piece.is_white == False):
            self.board[end[0]][end[1]] = piece
            self.board[start[0]][start[1]] = ''

    def get_move_notation(self, start, end):
        file_from = chr(ord('a') + start[1])
        rank_from = 8 - start[0]
        file_to = chr(ord('a') + end[1])
        rank_to = 8 - end[0]
        return f"{file_from}{rank_from} to {file_to}{rank_to}"

    def print_board(self):
        for row in self.board:
            print(' '.join([str(piece) if piece else '-' for piece in row]))

class AIPlayer:
    def __init__(self, color):
        self.color = color

    def make_move(self, chess_board):
        # Random move selection
        available_moves = chess_board.get_available_moves(chess_board.current_player)
        move = random.choice(available_moves)
        chess_board.move_piece(move)

    def play_game(self, chess_board):
        while True:
            self.make_move(chess_board)
            if chess_board.is_game_over():
                break

def main():
    # Initialize the chess board
    chess_board = ChessBoard()

    # Initialize AI players
    player1 = AIPlayer("White")
    player2 = AIPlayer("Black")

    # Open a file to save the game moves
    with open(FILE_NAME, 'w') as file:
        move_number = 1

        while not chess_board.is_game_over():
            # Player 1's turn
            if chess_board.current_player == "White":
                print(f"Move {move_number}: White's turn")
                player1.play_game(chess_board)
                for i in range(8):
                    for j in range(8):
                        move = (i, j)
                        if chess_board.board[i][j] != '':
                            file.write(f"{move_number}. {chess_board.get_move_notation(move, (i+1, j))}\n")
                            move_number += 1
            else:
                # Player 2's turn
                print(f"Move {move_number}: Black's turn")
                player2.play_game(chess_board)
                for i in range(8):
                    for j in range(8):
                        move = (i, j)
                        if chess_board.board[i][j] != '':
                            file.write(f"{move_number}. {chess_board.get_move_notation(move, (i+1, j))}\n")
                            move_number += 1

            # Print the current state of the board
            chess_board.print_board()

    # Game over, print the final result
    winner = "White" if chess_board.current_player == "Black" else "Black"
    print(f"Game Over! {winner} wins.")
    file.write(f"\nGame Over! {winner} wins.")

if __name__ == "__main__":
    main()