import pygame
import sys
import time

import tictactoe as ttt
import maze_escape


pygame.init()

# Window size
size = width, height = 900, 700
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Neon Game Hub")

clock = pygame.time.Clock()


# -----------------------------
# Color palette
# -----------------------------
BACKGROUND_TOP = (13, 18, 42)
BACKGROUND_BOTTOM = (33, 18, 55)

PANEL_COLOR = (28, 35, 69)
PANEL_BORDER = (75, 92, 150)

TILE_COLOR = (37, 47, 86)
TILE_HOVER_COLOR = (55, 67, 115)
TILE_BORDER = (94, 113, 185)

WHITE = (240, 245, 255)
TEXT_MUTED = (175, 187, 220)

X_COLOR = (80, 225, 255)
O_COLOR = (255, 104, 180)
WIN_COLOR = (255, 221, 87)

BUTTON_COLOR = (95, 79, 210)
BUTTON_HOVER_COLOR = (124, 106, 245)
BUTTON_TEXT = (255, 255, 255)

SHADOW_COLOR = (5, 8, 20)


# -----------------------------
# Fonts
# -----------------------------
try:
    smallFont = pygame.font.Font("OpenSans-Regular.ttf", 20)
    mediumFont = pygame.font.Font("OpenSans-Regular.ttf", 28)
    largeFont = pygame.font.Font("OpenSans-Regular.ttf", 42)
    moveFont = pygame.font.Font("OpenSans-Regular.ttf", 82)
except FileNotFoundError:
    smallFont = pygame.font.SysFont("arial", 20)
    mediumFont = pygame.font.SysFont("arial", 28, bold=True)
    largeFont = pygame.font.SysFont("arial", 42, bold=True)
    moveFont = pygame.font.SysFont("arial", 82, bold=True)


def draw_background():
    """
    Draw a vertical dark-blue/purple gradient background.
    """
    for y in range(height):
        ratio = y / height

        red = int(BACKGROUND_TOP[0] * (1 - ratio) + BACKGROUND_BOTTOM[0] * ratio)
        green = int(BACKGROUND_TOP[1] * (1 - ratio) + BACKGROUND_BOTTOM[1] * ratio)
        blue = int(BACKGROUND_TOP[2] * (1 - ratio) + BACKGROUND_BOTTOM[2] * ratio)

        pygame.draw.line(screen, (red, green, blue), (0, y), (width, y))


def draw_centered_text(text, font, color, center):
    """
    Draw text centered at a given position.
    """
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center)
    screen.blit(text_surface, text_rect)
    return text_rect


def draw_button(rect, text, mouse_position, font=mediumFont):
    """
    Draw a rounded button with a hover effect.
    """
    hovering = rect.collidepoint(mouse_position)

    pygame.draw.rect(screen, SHADOW_COLOR, rect.move(0, 5), border_radius=14)

    color = BUTTON_HOVER_COLOR if hovering else BUTTON_COLOR
    pygame.draw.rect(screen, color, rect, border_radius=14)

    pygame.draw.rect(screen, WHITE, rect, width=2, border_radius=14)

    draw_centered_text(text, font, BUTTON_TEXT, rect.center)


def winning_cells(current_board):
    """
    Return the three coordinates of a winning line, or None.
    """
    possible_lines = [
        [(0, 0), (0, 1), (0, 2)],
        [(1, 0), (1, 1), (1, 2)],
        [(2, 0), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (2, 0)],
        [(0, 1), (1, 1), (2, 1)],
        [(0, 2), (1, 2), (2, 2)],
        [(0, 0), (1, 1), (2, 2)],
        [(0, 2), (1, 1), (2, 0)],
    ]

    for line in possible_lines:
        first_row, first_col = line[0]
        second_row, second_col = line[1]
        third_row, third_col = line[2]

        first = current_board[first_row][first_col]
        second = current_board[second_row][second_col]
        third = current_board[third_row][third_col]

        if first is not ttt.EMPTY and first == second == third:
            return line

    return None


def draw_board(current_board, mouse_position):
    """
    Draw the Tic-Tac-Toe board and return clickable tile rectangles.
    """
    tile_size = 150
    gap = 12
    board_size = tile_size * 3 + gap * 2

    start_x = width // 2 - board_size // 2
    start_y = 200

    tiles = []
    game_over = ttt.terminal(current_board)
    win_line = winning_cells(current_board)

    panel_padding = 25
    panel_rect = pygame.Rect(
        start_x - panel_padding,
        start_y - panel_padding,
        board_size + panel_padding * 2,
        board_size + panel_padding * 2,
    )

    pygame.draw.rect(screen, SHADOW_COLOR, panel_rect.move(0, 8), border_radius=25)
    pygame.draw.rect(screen, PANEL_COLOR, panel_rect, border_radius=25)
    pygame.draw.rect(screen, PANEL_BORDER, panel_rect, width=2, border_radius=25)

    for i in range(3):
        row = []

        for j in range(3):
            x = start_x + j * (tile_size + gap)
            y = start_y + i * (tile_size + gap)

            rect = pygame.Rect(x, y, tile_size, tile_size)
            row.append(rect)

            cell_is_empty = current_board[i][j] == ttt.EMPTY
            hovering = rect.collidepoint(mouse_position)

            if hovering and cell_is_empty and not game_over:
                tile_color = TILE_HOVER_COLOR
            else:
                tile_color = TILE_COLOR

            if win_line is not None and (i, j) in win_line:
                tile_color = (102, 88, 47)

            pygame.draw.rect(screen, SHADOW_COLOR, rect.move(0, 4), border_radius=16)
            pygame.draw.rect(screen, tile_color, rect, border_radius=16)
            pygame.draw.rect(screen, TILE_BORDER, rect, width=2, border_radius=16)

            if current_board[i][j] != ttt.EMPTY:
                mark = current_board[i][j]
                mark_color = X_COLOR if mark == ttt.X else O_COLOR

                mark_surface = moveFont.render(mark, True, mark_color)
                mark_rect = mark_surface.get_rect(center=rect.center)
                screen.blit(mark_surface, mark_rect)

        tiles.append(row)

    if win_line is not None:
        first_row, first_col = win_line[0]
        last_row, last_col = win_line[2]

        first_center = tiles[first_row][first_col].center
        last_center = tiles[last_row][last_col].center

        pygame.draw.line(screen, WIN_COLOR, first_center, last_center, width=8)

    return tiles


def draw_header(title, subtitle=""):
    """
    Draw the Tic-Tac-Toe header and status panel.
    """
    draw_centered_text("TIC-TAC-TOE", largeFont, WHITE, (width // 2, 55))
    draw_centered_text("Minimax AI Challenge", smallFont, TEXT_MUTED, (width // 2, 94))

    status_rect = pygame.Rect(width // 2 - 260, 120, 520, 54)

    pygame.draw.rect(screen, SHADOW_COLOR, status_rect.move(0, 4), border_radius=14)
    pygame.draw.rect(screen, PANEL_COLOR, status_rect, border_radius=14)
    pygame.draw.rect(screen, PANEL_BORDER, status_rect, width=2, border_radius=14)

    draw_centered_text(title, mediumFont, WHITE, status_rect.center)

    if subtitle:
        draw_centered_text(subtitle, smallFont, TEXT_MUTED, (width // 2, 650))


def run_tictactoe():
    """
    Run the Tic-Tac-Toe game.

    Return to the main menu when the user clicks Main Menu.
    """
    user = None
    board = ttt.initial_state()
    ai_turn = False

    while True:
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

        draw_background()

        # Symbol selection screen
        if user is None:
            draw_centered_text("TIC-TAC-TOE", largeFont, WHITE, (width // 2, 125))
            draw_centered_text(
                "Choose a side and challenge the Minimax AI",
                mediumFont,
                TEXT_MUTED,
                (width // 2, 175),
            )

            selection_panel = pygame.Rect(width // 2 - 320, 230, 640, 260)

            pygame.draw.rect(screen, SHADOW_COLOR, selection_panel.move(0, 8), border_radius=25)
            pygame.draw.rect(screen, PANEL_COLOR, selection_panel, border_radius=25)
            pygame.draw.rect(screen, PANEL_BORDER, selection_panel, width=2, border_radius=25)

            draw_centered_text("Choose your symbol", mediumFont, WHITE, (width // 2, 275))

            play_x_button = pygame.Rect(width // 2 - 270, 335, 240, 75)
            play_o_button = pygame.Rect(width // 2 + 30, 335, 240, 75)
            menu_button = pygame.Rect(width // 2 - 120, 540, 240, 48)

            draw_button(play_x_button, "Play as X", mouse)
            draw_button(play_o_button, "Play as O", mouse)
            draw_button(menu_button, "Main Menu", mouse, smallFont)

            draw_centered_text(
                "The AI searches possible outcomes and plays optimally.",
                smallFont,
                TEXT_MUTED,
                (width // 2, 500),
            )

            click, _, _ = pygame.mouse.get_pressed()

            if click == 1:
                if play_x_button.collidepoint(mouse):
                    pygame.time.wait(180)
                    user = ttt.X

                elif play_o_button.collidepoint(mouse):
                    pygame.time.wait(180)
                    user = ttt.O

                elif menu_button.collidepoint(mouse):
                    pygame.time.wait(180)
                    return

        # Game screen
        else:
            game_over = ttt.terminal(board)
            current_player = ttt.player(board)
            game_winner = ttt.winner(board)

            if game_over:
                if game_winner is None:
                    title = "Game Over: It's a tie!"
                    subtitle = "Perfect play from both sides."
                elif game_winner == user:
                    title = f"Game Over: {game_winner} wins!"
                    subtitle = "You defeated the AI."
                else:
                    title = f"Game Over: {game_winner} wins!"
                    subtitle = "The Minimax AI found the winning path."

            elif user == current_player:
                title = f"Your turn — play as {user}"
                subtitle = "Choose an empty square."

            else:
                title = "AI is thinking..."
                subtitle = "The Minimax AI is evaluating future moves."

            draw_header(title, subtitle)
            tiles = draw_board(board, mouse)

            menu_button = pygame.Rect(30, height - 65, 170, 42)
            draw_button(menu_button, "Main Menu", mouse, smallFont)

            # AI move
            if user != current_player and not game_over:
                if ai_turn:
                    pygame.time.wait(350)
                    move = ttt.minimax(board)
                    board = ttt.result(board, move)
                    ai_turn = False
                else:
                    ai_turn = True

            click, _, _ = pygame.mouse.get_pressed()

            # Player move
            if click == 1 and user == current_player and not game_over:
                for i in range(3):
                    for j in range(3):
                        if board[i][j] == ttt.EMPTY and tiles[i][j].collidepoint(mouse):
                            board = ttt.result(board, (i, j))
                            pygame.time.wait(120)

            # Main menu button
            if click == 1 and menu_button.collidepoint(mouse):
                pygame.time.wait(180)
                return

            # Restart button after a completed game
            if game_over:
                again_button = pygame.Rect(width // 2 - 135, 580, 270, 52)
                draw_button(again_button, "Play Again", mouse)

                if click == 1 and again_button.collidepoint(mouse):
                    pygame.time.wait(180)
                    user = None
                    board = ttt.initial_state()
                    ai_turn = False

        pygame.display.flip()
        clock.tick(60)


def run_main_menu():
    """
    Display the game hub menu.

    Returns:
        "tictactoe" when Tic-Tac-Toe is selected,
        "maze" when Maze Escape is selected,
        "quit" when the application should close.
    """
    while True:
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

        draw_background()

        draw_centered_text("NEON GAME HUB", largeFont, WHITE, (width // 2, 120))
        draw_centered_text(
            "Choose a game and challenge its AI",
            mediumFont,
            TEXT_MUTED,
            (width // 2, 170),
        )

        menu_panel = pygame.Rect(width // 2 - 330, 225, 660, 300)

        pygame.draw.rect(screen, SHADOW_COLOR, menu_panel.move(0, 8), border_radius=25)
        pygame.draw.rect(screen, PANEL_COLOR, menu_panel, border_radius=25)
        pygame.draw.rect(screen, PANEL_BORDER, menu_panel, width=2, border_radius=25)

        tic_tac_toe_button = pygame.Rect(width // 2 - 260, 280, 520, 80)
        maze_button = pygame.Rect(width // 2 - 260, 385, 520, 80)

        draw_button(tic_tac_toe_button, "Tic-Tac-Toe — Minimax AI", mouse)
        draw_button(maze_button, "Maze Escape — BFS Hunter AI", mouse)

        draw_centered_text(
            "Tic-Tac-Toe: defeat or tie an optimal Minimax player.",
            smallFont,
            TEXT_MUTED,
            (width // 2, 550),
        )
        draw_centered_text(
            "Maze Escape: collect the key and evade a BFS pathfinding hunter.",
            smallFont,
            TEXT_MUTED,
            (width // 2, 580),
        )

        click, _, _ = pygame.mouse.get_pressed()

        if click == 1:
            if tic_tac_toe_button.collidepoint(mouse):
                pygame.time.wait(180)
                return "tictactoe"

            if maze_button.collidepoint(mouse):
                pygame.time.wait(180)
                return "maze"

        pygame.display.flip()
        clock.tick(60)


# -----------------------------
# Application loop
# -----------------------------
while True:
    choice = run_main_menu()

    if choice == "quit":
        pygame.quit()
        sys.exit()

    if choice == "tictactoe":
        run_tictactoe()

    elif choice == "maze":
        maze_escape.run(screen, clock)