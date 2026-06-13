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
    'K': 'King',
    'Q': 'Queen',
    'R': 'Rook',
    'B': 'Bishop',
    'N': 'Knight',
    'P': 'Pawn'
}

FILE_NAME = "chess_game.txt"


class Pawn:
    def __init__(self, color):
        self.color = color
        self.type = 'p'

    def get_moves(self, position, board):
        moves = []
        if self.color == 'w':
            if position[1] < 7 and board[position[0], position[1]+1] is None:
                moves.append((position[0], position[1]+1))
            if position[1] == 1 and board[position[0], position[1]+2] is None:
                moves.append((position[0], position[1]+2))
        else:
            if position[1] > 0 and board[position[0], position[1]-1] is None:
                moves.append((position[0], position[1]-1))
            if position[1] == 6 and board[position[0], position[1]-2] is None:
                moves.append((position[0], position[1]-2))
        return moves

class Knight:
    def __init__(self, color):
        self.color = color
        self.type = 'n'

    def get_moves(self, position, board):
        moves = []
        directions = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2)]
        for dx, dy in directions:
            new_x, new_y = position[0] + dx, position[1] + dy
            if 0 <= new_x < 8 and 0 <= new_y < 8:
                if board[new_x, new_y] is None or board[new_x, new_y].color != self.color:
                    moves.append((new_x, new_y))
        return moves

class Bishop:
    def __init__(self, color):
        self.color = color
        self.type = 'b'

    def get_moves(self, position, board):
        moves = []
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dx, dy in directions:
            x, y = position[0], position[1]
            while True:
                x += dx
                y += dy
                if not (0 <= x < 8 and 0 <= y < 8):
                    break
                if board[x, y] is None:
                    moves.append((x, y))
                elif board[x, y].color != self.color:
                    moves.append((x, y))
                    break
                else:
                    break
        return moves

class Rook:
    def __init__(self, color):
        self.color = color
        self.type = 'r'

    def get_moves(self, position, board):
        moves = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dx, dy in directions:
            x, y = position[0], position[1]
            while True:
                x += dx
                y += dy
                if not (0 <= x < 8 and 0 <= y < 8):
                    break
                if board[x, y] is None:
                    moves.append((x, y))
                elif board[x, y].color != self.color:
                    moves.append((x, y))
                    break
                else:
                    break
        return moves

class Queen:
    def __init__(self, color):
        self.color = color
        self.type = 'q'

    def get_moves(self, position, board):
        moves = []
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
        for dx, dy in directions:
            x, y = position[0], position[1]
            while True:
                x += dx
                y += dy
                if not (0 <= x < 8 and 0 <= y < 8):
                    break
                if board[x, y] is None:
                    moves.append((x, y))
                elif board[x, y].color != self.color:
                    moves.append((x, y))
                    break
                else:
                    break
        return moves

class King:
    def __init__(self, color):
        self.color = color
        self.type = 'k'

    def get_moves(self, position, board):
        moves = []
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dx, dy in directions:
            new_x, new_y = position[0] + dx, position[1] + dy
            if 0 <= new_x < 8 and 0 <= new_y < 8:
                if board[new_x, new_y] is None or board[new_x, new_y].color != self.color:
                    moves.append((new_x, new_y))
        return moves


class ChessBoard:
    def __init__(self):
        self.board = [['' for _ in range(8)] for _ in range(8)]
        self.initialize_board()
    
    def initialize_board(self):
        piece_positions = {
            'p': Pawn('black'), 'n': Knight('black'), 'b': Bishop('black'), 
            'r': Rook('black'), 'q': Queen('black'), 'k': King('black'),
            'P': Pawn('white'), 'N': Knight('white'), 'B': Bishop('white'), 
            'R': Rook('white'), 'Q': Queen('white'), 'K': King('white')
        }
        
        for i in range(8):
            if i == 0 or i == 7:
                self.board[i][0] = piece_positions['r']
                self.board[i][1] = piece_positions['n']
                self.board[i][2] = piece_positions['b']
                self.board[i][3] = piece_positions['q']
                self.board[i][4] = piece_positions['k']
                self.board[i][5] = piece_positions['b']
                self.board[i][6] = piece_positions['n']
                self.board[i][7] = piece_positions['r']
            else:
                for j in range(8):
                    if i < 2:
                        self.board[i][j] = piece_positions[PIECE_TYPES[j]]
                    elif i > 5:
                        self.board[i][j] = piece_positions[PIECE_TYPES[j].lower()]
    
    def get_piece(self, row, col):
        return self.board[row][col]
    
    def move_piece(self, from_pos, to_pos):
        piece = self.get_piece(*from_pos)
        if piece:
            self.board[to_pos[0]][to_pos[1]] = piece
            self.board[from_pos[0]][from_pos[1]] = ''
    
    def print_board(self):
        for row in self.board:
            print(' '.join([str(piece) if piece else '.' for piece in row]))

class Piece:
    def __init__(self, color):
        self.color = color
    
    def __str__(self):
        return PIECE_TYPES[type(self).__name__]

class Pawn(Piece): pass
class Knight(Piece): pass
class Bishop(Piece): pass
class Rook(Piece): pass
class Queen(Piece): pass
class King(Piece): pass

def get_move_notation(from_pos, to_pos):
    file = chr(ord('a') + from_pos[1])
    rank = 8 - from_pos[0]
    target_file = chr(ord('a') + to_pos[1])
    target_rank = 8 - to_pos[0]
    return f"{file}{rank}->{target_file}{target_rank}"

def print_board():
    board.print_board()

# Constants and Imports
PIECE_TYPES = {
    'Pawn': 'p', 'Knight': 'n', 'Bishop': 'b', 
    'Rook': 'r', 'Queen': 'q', 'King': 'k'
}
MOVE_NOTATION = []
FILE_NAME = "chess_moves.txt"


class AIPlayer:
    def __init__(self, piece_type):
        self.piece_type = piece_type

    def make_move(self, chess_board):
        # Logic for making a move based on piece type and chess board state
        # ...

        # Return the move in chess notation
        return move_notation

def play_game(ai_player1, ai_player2):
    chess_board = ChessBoard()

    while True:
        # AI player 1 makes a move
        move_notation = ai_player1.make_move(chess_board)
        chess_board.move_piece(move_notation)

        # Print the updated board
        print_board(chess_board)

        # Check if the game is over
        if chess_board.is_game_over():
            break

        # AI player 2 makes a move
        move_notation = ai_player2.make_move(chess_board)
        chess_board.move_piece(move_notation)

        # Print the updated board
        print_board(chess_board)

    # Print the game results
    print("Game over!")


# 
# Section 01
# Assignment 2
# Due: October 3, 2019
# This program simulates a chess game between two players. It will use pygame to simulate the board and pieces.

import pygame as pg
from pygame import *
import os
import sys

# CONSTANTS
PIECE_TYPES = {
    'P': ['pawn', 1, 60],
    'K': ['king', 2, 90],
    'Q': ['queen', 3, 90],
    'B': ['bishop', 4, 70],
    'N': ['knight', 5, 80],
    'R': ['rook', 6, 50]
}

MOVE_NOTATION = {
    'P': [1, 2, 3, 4, 5, 6, 7, 8],
    'K': [-1, -1, 0, 1, 1, 1, 1, -1],
    'Q': [-1, -1, -1, -1, -1, -1, -1, -1],
    'B': [1, 2, 3, 4, 5, 6, 7, 8],
    'N': [1, 2, 3, 4, 5, 6, 7, 8],
    'R': [-1, -1, -1, -1, -1, -1, -1, -1]
}

FILE_NAME = "chess_moves.txt"


class ChessBoard:

    def __init__(self):
        self.board = [[0 for i in range(8)] for j in range(8)]
        self.turn = 1

    # This function will return the move notation of a given piece
    @staticmethod
    def get_move_notation(piece, x, y):
        if piece == 'P':
            return MOVE_NOTATION[piece][y]
        elif piece == 'K' or piece == 'Q' or piece == 'R' or piece == 'B' or piece == 'N':
            return MOVE_NOTATION[piece][x] + str(MOVE_NOTATION[piece][y])

    # This function will print the board
    def print_board(self):
        for row in self.board:
            print(row)


class Piece:

    def __init__(self, piece, x, y):
        self.piece = piece
        self.x = x
        self.y = y

    # This function will return the move notation of a given piece
    @staticmethod
    def get_move_notation(piece, x, y):
        if piece == 'P':
            return MOVE_NOTATION[piece][y]
        elif piece == 'K' or piece == 'Q' or piece == 'R' or piece == 'B' or piece == 'N':
            return MOVE_NOTATION[piece][x] + str(MOVE_NOTATION[piece][y])


class AIPlayer:

    def __init__(self, player):
        self.player = player

    # This function will make a move
    def make_move(self, board):
        if self.player == 1:
            return [2, 3]
        elif self.player == 2:
            return [5, 4]


# This function will play the game
def play_game():

    # Initialize pygame
    pg.init()

    # Create a screen
    screen = pg.display.set_mode((600, 600))

    # Set the title of the window
    pg.display.set_caption('Chess')

    # Set the background color
    screen.fill(pg.Color("white"))

    # Draw the board
    for i in range(8):
        for j in range(8):
            if (i + j) % 2 == 0:
                pg.draw.rect(screen, pg.Color("black"), Rect((j * 75), (i * 75), 75, 75))

    # Draw the pieces
    for piece in PIECE_TYPES:
        if piece != 'P':
            for i in range(8):
                for j in range(8):
                    if board.board[j][i] == PIECE_TYPES[piece]:
                        pg.draw.circle(screen, pg.Color("black"), (j * 75 + 37.5, i * 75 + 37.5),
                                       int((PIECE_TYPES[piece][2]) / 10))

    # Update the screen
    pg.display.update()


# This function will save the game to a file
def save_game(board):
    with open(FILE_NAME, "a") as f:
        for i in range(8):
            for j in range(8):
                if board[j][i] != 0:
                    f.write(str(board[j][i]) + str(Piece.get_move_notation(board[j][i], j, i)) + "\n")


# This function will run the program
def main():
    # Create a chess board
    board = ChessBoard()

    # Play the game
    play_game()

    # Save the game to a file
    save_game(board)


main()