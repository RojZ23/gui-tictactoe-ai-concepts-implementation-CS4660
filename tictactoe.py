"""
Tic Tac Toe Player

Implements the rules for Tic-Tac-Toe and an optimal AI.

The AI uses Minimax with alpha-beta pruning and memoization.
It searches all possible future game states instead of using
hardcoded board positions such as always choosing the center.

The AI:
- Takes a forced win as quickly as possible.
- Blocks a forced loss whenever one can be blocked.
- Delays a loss if a loss is unavoidable.
- Randomly selects among moves that are equally optimal.
"""

import math
import random
from copy import deepcopy


# Board symbols
X = "X"
O = "O"
EMPTY = None


# All eight possible winning patterns.
WINNING_LINES = [
    # Rows
    ((0, 0), (0, 1), (0, 2)),
    ((1, 0), (1, 1), (1, 2)),
    ((2, 0), (2, 1), (2, 2)),

    # Columns
    ((0, 0), (1, 0), (2, 0)),
    ((0, 1), (1, 1), (2, 1)),
    ((0, 2), (1, 2), (2, 2)),

    # Diagonals
    ((0, 0), (1, 1), (2, 2)),
    ((0, 2), (1, 1), (2, 0)),
]


def initial_state():
    """
    Return a new empty 3 by 3 Tic-Tac-Toe board.
    """
    return [
        [EMPTY, EMPTY, EMPTY],
        [EMPTY, EMPTY, EMPTY],
        [EMPTY, EMPTY, EMPTY],
    ]


def player(board):
    """
    Return the player whose turn is next.

    X moves first. If both players have made the same number of
    moves, it is X's turn. Otherwise, it is O's turn.
    """
    x_count = sum(row.count(X) for row in board)
    o_count = sum(row.count(O) for row in board)

    return X if x_count == o_count else O


def actions(board):
    """
    Return a set of every legal action as (row, column).

    A position is legal only when it is empty.
    """
    return {
        (row, column)
        for row in range(3)
        for column in range(3)
        if board[row][column] == EMPTY
    }


def result(board, action):
    """
    Return a new board after the current player performs action.

    The original board is not modified.
    """
    if action not in actions(board):
        raise ValueError(f"Invalid action: {action}")

    new_board = deepcopy(board)
    row, column = action
    new_board[row][column] = player(board)

    return new_board


def winner(board):
    """
    Return X or O if either player has a winning line.

    Return None if no one has won.
    """
    for line in WINNING_LINES:
        (row1, col1), (row2, col2), (row3, col3) = line
        mark = board[row1][col1]

        if mark is not EMPTY and mark == board[row2][col2] == board[row3][col3]:
            return mark

    return None


def terminal(board):
    """
    Return True when the game has ended.

    The game is terminal when X wins, O wins, or no empty cells remain.
    """
    return winner(board) is not None or not actions(board)


def utility(board):
    """
    Return the basic utility of a terminal board.

    X win:  1
    O win: -1
    Tie:    0
    """
    game_winner = winner(board)

    if game_winner == X:
        return 1

    if game_winner == O:
        return -1

    return 0


def board_key(board):
    """
    Convert the board to an immutable value for the Minimax cache.
    """
    return tuple(tuple(row) for row in board)


def terminal_score(board, depth):
    """
    Return a depth-aware utility score for a terminal board.

    A large positive value means X wins.
    A large negative value means O wins.

    Depth makes the AI prefer:
    - Faster wins.
    - Slower losses.

    Examples:
    - An X win at depth 1 scores 99.
    - An X win at depth 5 scores 95.
    - An O win at depth 1 scores -99.
    - An O win at depth 5 scores -95.
    """
    game_winner = winner(board)

    if game_winner == X:
        return 100 - depth

    if game_winner == O:
        return -100 + depth

    return 0


def ordered_actions(board):
    """
    Return legal moves in a shuffled order.

    Shuffling prevents search order from always favoring the same
    location. It does not hardcode any board preference.

    Minimax still evaluates every important possible game outcome.
    """
    available_actions = list(actions(board))
    random.shuffle(available_actions)

    return available_actions


def max_value(board, alpha, beta, depth, cache):
    """
    Return the best score X can guarantee from board.

    X is the maximizing player.
    """
    key = board_key(board)

    if key in cache:
        return cache[key]

    if terminal(board):
        score = terminal_score(board, depth)
        cache[key] = score
        return score

    value = -math.inf

    for action in ordered_actions(board):
        child_value = min_value(
            result(board, action),
            alpha,
            beta,
            depth + 1,
            cache,
        )

        value = max(value, child_value)
        alpha = max(alpha, value)

        # O has a better choice higher in the tree, so stop searching.
        if alpha >= beta:
            break

    cache[key] = value
    return value


def min_value(board, alpha, beta, depth, cache):
    """
    Return the best score O can guarantee from board.

    O is the minimizing player.
    """
    key = board_key(board)

    if key in cache:
        return cache[key]

    if terminal(board):
        score = terminal_score(board, depth)
        cache[key] = score
        return score

    value = math.inf

    for action in ordered_actions(board):
        child_value = max_value(
            result(board, action),
            alpha,
            beta,
            depth + 1,
            cache,
        )

        value = min(value, child_value)
        beta = min(beta, value)

        # X has a better choice higher in the tree, so stop searching.
        if alpha >= beta:
            break

    cache[key] = value
    return value


def minimax(board):
    """
    Return a randomly selected optimal action for the current player.

    X maximizes the score and O minimizes it. The algorithm searches
    the game tree to terminal boards and uses alpha-beta pruning to
    avoid unnecessary work.

    There are no hardcoded moves. If multiple actions lead to the same
    best outcome, one is randomly selected for varied gameplay.
    """
    if terminal(board):
        return None

    current_player = player(board)
    cache = {}
    best_actions = []

    if current_player == X:
        best_score = -math.inf

        for action in ordered_actions(board):
            score = min_value(
                result(board, action),
                -math.inf,
                math.inf,
                1,
                cache,
            )

            if score > best_score:
                best_score = score
                best_actions = [action]

            elif score == best_score:
                best_actions.append(action)

    else:
        best_score = math.inf

        for action in ordered_actions(board):
            score = max_value(
                result(board, action),
                -math.inf,
                math.inf,
                1,
                cache,
            )

            if score < best_score:
                best_score = score
                best_actions = [action]

            elif score == best_score:
                best_actions.append(action)

    return random.choice(best_actions)