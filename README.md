# Tic-Tac-Toe AI Lab: Adversarial Search

In this lab, I built a Tic-Tac-Toe AI in Python using the **Minimax algorithm**. The purpose of the lab was to learn how an AI can evaluate possible future moves, predict an opponent’s choices, and select the best move instead of making a random decision.

## Tools and Files Used

- Python 3.12  
- Pygame graphical interface  
- `tictactoe.py` for the game logic and AI implementation  
- `runner.py` for the provided graphical game interface  
- `requirements.txt` to install the required Pygame package  
- A 3 × 3 Tic-Tac-Toe board represented as a list of lists  
- Board values: `X`, `O`, and `EMPTY`  
- Row-and-column actions represented as tuples, such as `(1, 2)`  

## What I Implemented

I completed the required functions in `tictactoe.py` so the game could correctly represent a board, identify legal moves, detect wins and ties, and make optimal AI decisions.

- `player(board)` determines whose turn it is by counting the number of X and O marks already on the board. X always moves first, and the players alternate turns.
- `actions(board)` finds all available empty cells and returns them as legal `(row, column)` actions.
- `result(board, action)` creates a new board after a player makes a move. I made sure it copies the original board instead of changing it directly, because Minimax needs separate board states for every possible branch of the search.
- `winner(board)` checks for horizontal, vertical, and diagonal three-in-a-row wins.
- `terminal(board)` determines whether the game is finished because X won, O won, or the board is full.
- `utility(board)` assigns a value to completed games: `1` when X wins, `-1` when O wins, and `0` for a tie.
- `minimax(board)` explores possible future board states and returns the best legal move for the current player.

## How the AI Works

The AI uses Minimax to search through possible future moves until it reaches a terminal board. A terminal board is a completed game where X wins, O wins, or the game ends in a tie.

X is the maximizing player, so it chooses moves that lead to the highest possible utility value. O is the minimizing player, so it chooses moves that lead to the lowest possible utility value.

| Game outcome | Utility value | AI goal |
|---|---:|---|
| X wins | 1 | X tries to maximize this result |
| Tie | 0 | Both players may settle for this if a win is impossible |
| O wins | -1 | O tries to minimize the result |

For example, if X has a move that guarantees a win, Minimax selects that move because it produces utility `1`. If O has a move that blocks X from winning, O selects the move that produces the lowest possible outcome for X.

## What I Did and Learned

One challenge was understanding how the functions work together. At first, functions such as `player`, `actions`, `result`, `winner`, `terminal`, and `utility` seemed separate, but Minimax depends on every one of them being correct. If the current player is identified incorrectly, the AI can place the wrong mark. If legal actions include occupied cells, the AI can attempt invalid moves. If terminal states are not detected correctly, the algorithm can continue exploring a game that has already ended.

Another important part was preserving the original board in `result(board, action)`. Since Minimax explores many possible futures, directly changing one board could affect other branches of the search tree. I used a copied board for each action so every successor state remained independent.

I also learned how recursion allows Minimax to look beyond the next move. The algorithm repeatedly explores future actions until it reaches a win, loss, or tie. It then returns the utility value back through the recursive calls. At each level, X selects the maximum available value and O selects the minimum available value.

## Testing and Extra Practice

I tested the program with different game situations, including:

- X moving first and alternating turns with O  
- Horizontal, vertical, and diagonal wins  
- Tie games  
- Invalid moves  
- Boards with one remaining legal move  
- Terminal boards  
- Situations where the AI must block an opponent’s winning move  
- Situations where the AI should take its own winning move  
- Verification that `result()` does not modify the original board  

When the program was complete, I ran `runner.py` to play against the AI through the Pygame interface. If both the player and AI make the best possible moves, the game should end in a tie. The AI should not be beatable when it is playing optimally.

For extra practice, I also worked with a game called **Maze Escape**. Although it is different from Tic-Tac-Toe, it uses many of the same AI ideas: representing states, identifying valid actions, generating successor states, checking goal or terminal conditions, and choosing actions in a game environment. Comparing Maze Escape with Tic-Tac-Toe helped me better understand how AI search concepts can apply to different kinds of games.
