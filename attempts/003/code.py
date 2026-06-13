# Constants and Imports

PIECE_TYPES = {
    'pawn': 'p',
    'knight': 'n',
    'bishop': 'b',
    'rook': 'r',
    'queen': 'q',
    'king': 'k'
}

MOVE_NOTATION = {
    'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7,
    0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'
}

FILE_NAME = "chess_game.txt"


class Piece:
    def __init__(self, color):
        self.color = color
        self.symbol = None

    def get_moves(self, board, position):
        pass

class Pawn(Piece):
    symbol = 'p' if 'white' in self.color else 'P'

    def get_moves(self, board, position):
        moves = []
        row, col = position
        direction = 1 if 'white' in self.color else -1
        if board[row + direction][col] is None:
            moves.append((row + direction, col))
        if row == (0 if 'white' in self.color else 7):
            moves.extend([(row + 2 * direction, col), (row + direction, col)])
        for offset in [-1, 1]:
            if 0 <= col + offset < 8 and board[row + direction][col + offset] is not None:
                moves.append((row + direction, col + offset))
        return moves

class Knight(Piece):
    symbol = 'n' if 'white' in self.color else 'N'

    def get_moves(self, board, position):
        moves = []
        row, col = position
        for dr, dc in [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2)]:
            if 0 <= row + dr < 8 and 0 <= col + dc < 8:
                moves.append((row + dr, col + dc))
        return moves

class Bishop(Piece):
    symbol = 'b' if 'white' in self.color else 'B'

    def get_moves(self, board, position):
        moves = []
        row, col = position
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] is None:
                    moves.append((r, c))
                else:
                    if 'white' in self.color != 'white' in board[r][c].color:
                        moves.append((r, c))
                    break
                r += dr
                c += dc
        return moves

class Rook(Piece):
    symbol = 'r' if 'white' in self.color else 'R'

    def get_moves(self, board, position):
        moves = []
        row, col = position
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] is None:
                    moves.append((r, c))
                else:
                    if 'white' in self.color != 'white' in board[r][c].color:
                        moves.append((r, c))
                    break
                r += dr
                c += dc
        return moves

class Queen(Piece):
    symbol = 'q' if 'white' in self.color else 'Q'

    def get_moves(self, board, position):
        moves = []
        row, col = position
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] is None:
                    moves.append((r, c))
                else:
                    if 'white' in self.color != 'white' in board[r][c].color:
                        moves.append((r, c))
                    break
                r += dr
                c += dc
        return moves

class King(Piece):
    symbol = 'k' if 'white' in self.color else 'K'

    def get_moves(self, board, position):
        moves = []
        row, col = position
        for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            if 0 <= row + dr < 8 and 0 <= col + dc < 8:
                moves.append((row + dr, col + dc))
        return moves


class Piece:
    PIECE_TYPES = {
        'p': 'Pawn',
        'n': 'Knight',
        'b': 'Bishop',
        'r': 'Rook',
        'q': 'Queen',
        'k': 'King'
    }
    
    def __init__(self, color, piece_type):
        self.color = color
        self.piece_type = piece_type
    
    def __str__(self):
        return f"{self.color[0].upper()}{self.piece_type}"

class ChessBoard:
    FILES = "abcdefgh"
    RANKS = "12345678"
    
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
    
    def add_piece(self, file, rank, piece):
        index_file = self.FILES.index(file)
        index_rank = 8 - int(rank)
        self.board[index_rank][index_file] = piece
    
    def remove_piece(self, file, rank):
        index_file = self.FILES.index(file)
        index_rank = 8 - int(rank)
        self.board[index_rank][index_file] = None
    
    def get_piece(self, file, rank):
        index_file = self.FILES.index(file)
        index_rank = 8 - int(rank)
        return self.board[index_rank][index_file]
    
    def print_board(self):
        for row in reversed(self.board):
            line = ""
            for piece in row:
                if piece is None:
                    line += ". "
                else:
                    line += str(piece) + " "
            print(line)
    
    def get_move_notation(self, move):
        from_file, from_rank = move['from']
        to_file, to_rank = move['to']
        return f"{from_file}{from_rank} {to_file}{to_rank}"

def main():
    board = ChessBoard()
    pieces = [
        ('a', '1', Piece('white', 'r')),  # Rook
        ('b', '1', Piece('white', 'n')),  # Knight
        ('c', '1', Piece('white', 'b')),  # Bishop
        ('d', '1', Piece('white', 'q')),  # Queen
        ('e', '1', Piece('white', 'k')),  # King
        ('f', '1', Piece('white', 'b')),  # Bishop
        ('g', '1', Piece('white', 'n')),  # Knight
        ('h', '1', Piece('white', 'r')),  # Rook
    ]
    for file, rank, piece in pieces:
        board.add_piece(file, rank, piece)
    
    pawns = [('a', '2', Piece('white', 'p')), ('b', '2', Piece('white', 'p')), 
             ('c', '2', Piece('white', 'p')), ('d', '2', Piece('white', 'p')),
             ('e', '2', Piece('white', 'p')), ('f', '2', Piece('white', 'p')),
             ('g', '2', Piece('white', 'p')), ('h', '2', Piece('white', 'p'))]
    for file, rank, piece in pawns:
        board.add_piece(file, rank, piece)
    
    # Add black pieces similarly
    
    board.print_board()
    move = {'from': ('a', '2'), 'to': ('a', '4')}  # Example move
    print(board.get_move_notation(move))

if __name__ == "__main__":
    main()


class AIPlayer:
    def __init__(self, color):
        self.color = color

    def make_move(self, chess_board):
        # Logic for making a move based on the AI strategy
        # ...

        # Return the move in chess notation
        return move_notation

    def play_game(self, chess_board):
        while True:
            # Get the move from the AI player
            move_notation = self.make_move(chess_board)

            # Update the chess board with the move
            chess_board.move_piece(move_notation)

            # Check if the game is over
            if chess_board.is_game_over():
                break

        # Return the game results
        return chess_board.game_result()


# 
# 10/27/18
# CS 361-400, Assignment 5
# This program creates a text based chess simulator that allows two AI players to play against each other.

import pygame
from pygame import *
import random
import math

# Constants and Imports
PIECE_TYPES = ['p', 'n', 'b', 'r', 'q', 'k']  # List of piece types for board representation
MOVE_NOTATION = {'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop', 'r': 'Rook', 'q': 'Queen', 'k': 'King'}  # Dictionary of move notation for each piece type
FILE_NAME = "chess_results.txt"  # File name to save results


# Chess Piece Classes
class Pawn:
    def __init__(self, color):
        self.color = color

    def get_moves(self, board, row, col):
        moves = []

        if self.color == 'w':
            if board[row - 1][col] is None and row > 0:
                moves.append((row - 1, col))

            if (board[row - 2][col] is None) and (row == 6):
                moves.append((row - 2, col))

            if board[row - 1][col + 1] is not None and board[row - 1][col + 1].color != self.color:
                moves.append((row - 1, col + 1))
            if board[row - 1][col - 1] is not None and board[row - 1][col - 1].color != self.color:
                moves.append((row - 1, col - 1))
        else:
            if board[row + 1][col] is None and row < 7:
                moves.append((row + 1, col))

            if (board[row + 2][col] is None) and (row == 1):
                moves.append((row + 2, col))

            if board[row + 1][col + 1] is not None and board[row + 1][col + 1].color != self.color:
                moves.append((row + 1, col + 1))
            if board[row + 1][col - 1] is not None and board[row + 1][col - 1].color != self.color:
                moves.append((row + 1, col - 1))

        return moves


class Knight(Pawn):
    def __init__(self, color):
        super().__init__(color)

    def get_moves(self, board, row, col):
        moves = []

        if self.color == 'w':
            for i in range(-2, 3):
                for j in range(-2, 3):
                    if (i != 0 or j != 0) and abs(i + j) == 1:
                        if row - 1 >= 0 and col + 1 < 8:
                            if board[row - 1][col + 1] is None:
                                moves.append((row - 1, col + 1))
                            elif board[row - 1][col + 1].color != self.color:
                                moves.append((row - 1, col + 1))
                        if row - 2 >= 0 and col + 2 < 8:
                            if board[row - 2][col + 2] is None:
                                moves.append((row - 2, col + 2))
                            elif board[row - 2][col + 2].color != self.color:
                                moves.append((row - 2, col + 2))
                        if row - 1 >= 0 and col - 1 > -1:
                            if board[row - 1][col - 1] is None:
                                moves.append((row - 1, col - 1))
                            elif board[row - 1][col - 1].color != self.color:
                                moves.append((row - 1, col - 1))
                        if row - 2 >= 0 and col - 2 > -1:
                            if board[row - 2][col - 2] is None:
                                moves.append((row - 2, col - 2))
                            elif board[row - 2][col - 2].color != self.color:
                                moves.append((row - 2, col - 2))
        else:
            for i in range(-2, 3):
                for j in range(-2, 3):
                    if (i != 0 or j != 0) and abs(i + j) == 1:
                        if row + 1 < 8 and col + 1 < 8:
                            if board[row + 1][col + 1] is None:
                                moves.append((row + 1, col + 1))
                            elif board[row + 1][col + 1].color != self.color:
                                moves.append((row + 1, col + 1))
                        if row + 2 < 8 and col + 2 < 8:
                            if board[row + 2][col + 2] is None:
                                moves.append((row + 2, col + 2))
                            elif board[row + 2][col + 2].color != self.color:
                                moves.append((row + 2, col + 2))
                        if row + 1 < 8 and col - 1 > -1:
                            if board[row + 1][col - 1] is None:
                                moves.append((row + 1, col - 1))
                            elif board[row + 1][col - 1].color != self.color:
                                moves.append((row + 1, col - 1))
                        if row + 2 < 8 and col - 2 > -1:
                            if board[row + 2][col - 2] is None:
                                moves.append((row + 2, col - 2))
                            elif board[row + 2][col - 2].color != self.color:
                                moves.append((row + 2, col - 2))

        return moves


class Bishop(Pawn):
    def __init__(self, color):
        super().__init__(color)

    def get_moves(self, board, row, col):
        moves = []

        if self.color == 'w':
            for i in range(-7, 8):
                for j in range(-7, 8):
                    if (i != 0 or j != 0) and abs(i + j) > 1:
                        if row - i >= 0 and col + j < 8:
                            if board[row - i][col + j] is None:
                                moves.append((row - i, col + j))
                            elif board[row - i][col + j].color != self.color:
                                moves.append((row - i, col + j))
        else:
            for i in range(-7, 8):
                for j in range(-7, 8):
                    if (i != 0 or j != 0) and abs(i + j) > 1:
                        if row + i < 8 and col + j < 8:
                            if board[row + i][col + j] is None:
                                moves.append((row + i, col + j))
                            elif board[row + i][col + j].color != self.color:
                                moves.append((row + i, col + j))

        return moves


class Rook(Pawn):
    def __init__(self, color):
        super().__init__(color)

    def get_moves(self, board, row, col):
        moves = []

        if self.color == 'w':
            for i in range(-7, 8):
                for j in range(-7, 8):
                    if (i != 0 or j != 0) and abs(i + j) < 1:
                        if row - i >= 0 and col + j < 8:
                            if board[row - i][col + j] is None:
                                moves.append((row - i, col + j))
                            elif board[row - i][col + j].color != self.color:
                                moves.append((row - i, col + j))
        else:
            for i in range(-7, 8):
                for j in range(-7, 8):
                    if (i != 0 or j != 0) and abs(i + j) < 1:
                        if row + i < 8 and col + j < 8:
                            if board[row + i][col + j] is None:
                                moves.append((row + i, col + j))
                            elif board[row + i][col + j].color != self.color:
                                moves.append((row + i, col + j))

        return moves


class Queen(Pawn):
    def __init__(self, color):
        super().__init__(color)

    def get_moves(self, board, row, col):
        moves = []

        if self.color == 'w':
            for i in range(-7, 8):
                for j in range(-7, 8):
                    if (i != 0 or j != 0) and abs(i + j) < 1:
                        if row - i >= 0 and col + j < 8:
                            if board[row - i][col + j] is None:
                                moves.append((row - i, col + j))
                            elif board[row - i][col + j].color != self.color:
                                moves.append((row - i, col + j))
        else:
            for i in range(-7, 8):
                for j in range(-7, 8):
                    if (i != 0 or j != 0) and abs(i + j) < 1:
                        if row + i < 8 and col + j < 8:
                            if board[row + i][col + j] is None:
                                moves.append((row + i, col + j))
                            elif board[row + i][col + j].color != self.color:
                                moves.append((row + i, col + j))

        for i in range(-7, 8):
            for j in range(-7, 8):
                if (i != 0 or j != 0) and abs(i + j) > 1:
                    if row - i >= 0 and col + j < 8:
                        if board[row - i][col + j] is None:
                            moves.append((row - i, col + j))
                        elif board[row - i][col + j].color != self.color:
                            moves.append((row - i, col + j))
        else:
            for i in range(-7, 8):
                for j in range(-7, 8):
                    if (i != 0 or j != 0) and abs(i + j) > 1:
                        if row + i < 8 and col + j < 8:
                            if board[row + i][col + j] is None:
                                moves.append((row + i, col + j))
                            elif board[row + i][col + j].color != self.color:
                                moves.append((row + i, col + j))

        return moves


class King(Pawn):
    def __init__(self, color):
        super().__init__(color)

    def get_moves(self, board, row, col):
        moves = []

        if self.color == 'w':
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if (i != 0 or j != 0) and abs(i + j) < 2:
                        if row - i >= 0 and col + j < 8:
                            if board[row - i][col + j] is None:
                                moves.append((row - i, col + j))
                            elif board[row - i][col + j].color != self.color:
                                moves.append((row - i, col + j))
        else:
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if (i != 0 or j != 0) and abs(i + j) < 2:
                        if row + i < 8 and col + j < 8:
                            if board[row + i][col + j] is None:
                                moves.append((row + i, col + j))
                            elif board[row + i][col + j].color != self.color:
                                moves.append((row + i, col + j))

        return moves


# Chess Board and Move Notation
class ChessBoard:
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]

    # Converts move notation to board coordinates
    @staticmethod
    def get_board_coords(move_notation):
        row = 0
        col = 0

        if len(move_notation) == 2:
            if move_notation[1].isnumeric():
                row = int(move_notation[1]) - 1
            else:
                col = PIECE_TYPES.index(move_notation[1])

            if move_notation[0] in 'abcdefgh':
                col = ord(move_notation[0]) - 97
        elif len(move_notation) == 3:
            if move_notation[2].isnumeric():
                row = int(move_notation[2]) - 1
            else:
                col = PIECE_TYPES.index(move_notation[2])

            if move_notation[0] in 'abcdefgh':
                col = ord(move_notation[0]) - 97
            elif move_notation[1] == 'x' and move_notation[0].isnumeric():
                row = int(move_notation[0]) - 1

        return row, col

    # Converts board coordinates to move notation
    @staticmethod
    def get_move_notation(row, col):
        if row < 8:
            if col < 8:
                return chr(col + 97) + str(row + 1)
            else:
                return str(row + 1)

    # Prints board to command line
    @staticmethod
    def print_board(board):
        for i in range(len(board)):
            if i % 2 == 0:
                print(' ', end='')

            for j in range(len(board[i])):
                if (j + i) % 2 != 0 and board[i][j] is not None:
                    print(board[i][j].color, end=' ')

                elif (j + i) % 2 == 0 and board[i][j] is not None:
                    print(' ', end='')
                else:
                    print('  ', end='')

            if i % 2 != 0:
                print()

    # Returns list of pieces in board
    def get_pieces(self):
        pieces = []

        for row in self.board:
            for piece in row:
                if piece is not None:
                    pieces.append(piece)

        return pieces


# AI Players and Game Logic
class AIPlayer:

    def __init__(self, color):
        self.color = color

    # Returns list of possible moves
    @staticmethod
    def get_moves(board, row, col):
        moves = []

        for i in range(-7, 8):
            for j in range(-7, 8):
                if (i != 0 or j != 0) and abs(i + j) < 1:
                    if row - i >= 0 and col + j < 8:
                        if board[row - i][col + j] is None:
                            moves.append((row - i, col + j))
                        elif board[row - i][col + j].color != board[row][col].color:
                            moves.append((row - i, col + j))
        else:
            for i in range(-7, 8):
                for j in range(-7, 8):
                    if (i != 0 or j != 0) and abs(i + j) < 1:
                        if row + i < 8 and col + j < 8:
                            if board[row + i][col + j] is None:
                                moves.append((row + i, col + j))
                            elif board[row + i][col + j].color != board[row][col].color:
                                moves.append((row + i, col + j))

        return moves

    # Returns list of possible pieces
    def get_pieces(self):
        pieces = []

        for row in self.board:
            for piece in row:
                if piece is not None and piece.color == self.color:
                    pieces.append(piece)

        return pieces


# Main Entry Point
def main():
    # Initialize pygame
    pygame.init()

    # Set window size to 800x600
    screen = pygame.display.set_mode((800, 600))

    # Set background color
    screen.fill(pygame.Color('white'))

    # Create board object
    board = ChessBoard()

    # Initialize player objects
    player1 = AIPlayer('w')
    player2 = AIPlayer('b')

    # Set starting position of pieces
    for i in range(8):
        board.board[i][0] = Pawn('b')
        board.board[i][7] = Pawn('w')

        if i == 1:
            board.board[i][1] = Knight('b')
            board.board[i][6] = Knight('w')
        elif i == 2:
            board.board[i][0] = Bishop('b')
            board.board[i][7] = Bishop('w')
        elif i == 3:
            board.board[i][1] = Rook('b')
            board.board[i][6] = Rook('w')
        elif i == 4:
            board.board[i][2] = Queen('b')
            board.board[i][5] = Queen('w')
        elif i == 5:
            board.board[i][3] = King('b')
            board.board[i][4] = King('w')

    # Set player1 and player2 pieces
    player1.board = board.board
    player2.board = board.board

    # Initialize clock object
    clock = pygame.time.Clock()

    # Game loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        # Draw board to screen
        ChessBoard.print_board(board.board)

        # Update display
        pygame.display.update()


if __name__ == '__main__':
    main()