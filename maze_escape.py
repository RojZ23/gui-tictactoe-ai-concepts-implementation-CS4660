"""
Maze Escape AI
==============

A randomized top-down maze game with a BFS-controlled hunter.

Goal:
    1. Collect the gold key.
    2. Open the locked door.
    3. Collect enough energy gems.
    4. Reach the green exit.

Controls:
    Arrow Keys / WASD : Move
    R                 : Generate a new maze
    Escape            : Return to the main menu

Gameplay:
    - The red hunter uses Breadth-First Search (BFS).
    - The hunter moves every few player turns.
    - Blue safe zones temporarily prevent the hunter from moving.
    - Switches can slow the hunter for several turns.
    - Extra loops and side corridors provide alternate escape routes.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Optional
import random

import pygame


# ---------------------------------------------------------------------------
# Maze symbols
# ---------------------------------------------------------------------------

WALL = "#"
FLOOR = "."
START = "S"
EXIT = "E"
KEY = "K"
ENEMY = "A"
DOOR = "D"
GEM = "G"
SAFE_ZONE = "O"
SWITCH = "T"

Position = tuple[int, int]


# ---------------------------------------------------------------------------
# Game balancing
# ---------------------------------------------------------------------------

MAZE_ROWS = 17
MAZE_COLS = 25

TILE_SIZE = 28
MIN_TILE_SIZE = 20
MAX_TILE_SIZE = 34

ENEMY_MOVES_EVERY = 3
SWITCH_SLOWDOWN_TURNS = 8
SAFE_ZONE_PROTECTION_TURNS = 2

GEMS_REQUIRED = 3
TOTAL_GEMS = 5

MIN_ROUTE_LENGTH = 26
MAX_GENERATION_ATTEMPTS = 80


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

BACKGROUND_TOP = (8, 12, 30)
BACKGROUND_BOTTOM = (48, 16, 68)

WALL_COLOR = (63, 48, 125)
WALL_EDGE = (145, 114, 230)
WALL_HIGHLIGHT = (99, 76, 181)

FLOOR_COLOR = (19, 28, 56)
FLOOR_GRID = (34, 46, 82)

PLAYER_COLOR = (73, 223, 255)
PLAYER_GLOW = (130, 242, 255)

ENEMY_COLOR = (255, 70, 108)
ENEMY_GLOW = (255, 145, 173)

KEY_COLOR = (255, 218, 73)
GEM_COLOR = (91, 245, 213)
GEM_GLOW = (143, 255, 234)

EXIT_LOCKED_COLOR = (136, 82, 57)
EXIT_OPEN_COLOR = (71, 226, 142)

DOOR_COLOR = (203, 131, 65)
DOOR_EDGE = (255, 196, 109)

SAFE_ZONE_COLOR = (75, 149, 255)
SAFE_ZONE_GLOW = (115, 196, 255)

SWITCH_COLOR = (255, 126, 226)
SWITCH_ACTIVE_COLOR = (136, 255, 195)

WHITE = (240, 246, 255)
TEXT_MUTED = (175, 188, 222)
WARNING_COLOR = (255, 190, 95)

PANEL_COLOR = (24, 32, 66)
PANEL_BORDER = (77, 99, 165)

BUTTON_COLOR = (93, 76, 210)
BUTTON_HOVER_COLOR = (127, 108, 248)
SHADOW_COLOR = (4, 7, 18)


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------

@dataclass
class GameState:
    """Stores all mutable information for one Maze Escape session."""

    maze: list[list[str]]
    player: Position
    enemy: Position
    exit: Position
    key: Position
    gems_required: int = GEMS_REQUIRED

    has_key: bool = False
    gems_collected: int = 0
    moves: int = 0

    game_over: bool = False
    won: bool = False

    enemy_slow_turns: int = 0
    safe_turns: int = 0
    enemy_pulse: int = 0

    message: str = "Find the key, collect energy gems, and reach the exit."
    message_color: tuple[int, int, int] = WHITE


# ---------------------------------------------------------------------------
# Maze helpers
# ---------------------------------------------------------------------------

def in_bounds(maze: list[list[str]], position: Position) -> bool:
    """Return True when a position is inside the maze grid."""
    row, column = position
    return 0 <= row < len(maze) and 0 <= column < len(maze[0])


def is_walkable(
    maze: list[list[str]],
    position: Position,
    has_key: bool = True,
) -> bool:
    """
    Return True when a position is a valid walkable tile.

    A locked door blocks movement until the player owns the key.
    """
    if not in_bounds(maze, position):
        return False

    row, column = position
    tile = maze[row][column]

    if tile == WALL:
        return False

    if tile == DOOR and not has_key:
        return False

    return True


def valid_neighbors(
    maze: list[list[str]],
    position: Position,
    has_key: bool = True,
) -> list[Position]:
    """Return all valid north, south, west, and east neighbors."""
    row, column = position

    candidates = [
        (row - 1, column),
        (row + 1, column),
        (row, column - 1),
        (row, column + 1),
    ]

    return [
        candidate
        for candidate in candidates
        if is_walkable(maze, candidate, has_key)
    ]


def bfs_path(
    maze: list[list[str]],
    start: Position,
    goal: Position,
    has_key: bool = True,
) -> list[Position]:
    """
    Return the shortest BFS path from start to goal.

    Returns an empty list if no route exists. The returned path includes both
    the start and goal positions.
    """
    if start == goal:
        return [start]

    queue = deque([start])
    came_from: dict[Position, Optional[Position]] = {start: None}

    while queue:
        current = queue.popleft()

        if current == goal:
            break

        for neighbor in valid_neighbors(maze, current, has_key):
            if neighbor not in came_from:
                came_from[neighbor] = current
                queue.append(neighbor)

    if goal not in came_from:
        return []

    path = []
    current: Optional[Position] = goal

    while current is not None:
        path.append(current)
        current = came_from[current]

    path.reverse()
    return path


def bfs_next_step(
    maze: list[list[str]],
    start: Position,
    goal: Position,
) -> Position:
    """
    Return the next BFS step for the hunter.

    The hunter ignores the door lock because it is an AI that can travel
    through the maze's internal routes. This keeps the door useful as a
    player puzzle without causing the hunter to get permanently stuck.
    """
    path = bfs_path(maze, start, goal, has_key=True)

    if len(path) < 2:
        return start

    return path[1]


def maze_distance(
    maze: list[list[str]],
    start: Position,
    goal: Position,
) -> int:
    """Return BFS distance between two points, or -1 if no route exists."""
    path = bfs_path(maze, start, goal, has_key=True)

    if not path:
        return -1

    return len(path) - 1


def random_odd_number(minimum: int, maximum: int) -> int:
    """Return a random odd number between minimum and maximum inclusive."""
    values = [value for value in range(minimum, maximum + 1) if value % 2 == 1]
    return random.choice(values)


# ---------------------------------------------------------------------------
# Random maze generation
# ---------------------------------------------------------------------------

def generate_base_maze(rows: int, columns: int) -> list[list[str]]:
    """
    Generate a perfect maze using randomized depth-first search.

    A perfect maze has one path between every pair of walkable cells. Extra
    walls are later removed to create loops and alternate routes.
    """
    maze = [[WALL for _ in range(columns)] for _ in range(rows)]

    start_row = 1
    start_column = 1

    maze[start_row][start_column] = FLOOR
    stack = [(start_row, start_column)]

    directions = [
        (-2, 0),
        (2, 0),
        (0, -2),
        (0, 2),
    ]

    while stack:
        row, column = stack[-1]
        random.shuffle(directions)

        carved = False

        for row_change, column_change in directions:
            next_row = row + row_change
            next_column = column + column_change

            if (
                1 <= next_row < rows - 1
                and 1 <= next_column < columns - 1
                and maze[next_row][next_column] == WALL
            ):
                wall_row = row + row_change // 2
                wall_column = column + column_change // 2

                maze[wall_row][wall_column] = FLOOR
                maze[next_row][next_column] = FLOOR

                stack.append((next_row, next_column))
                carved = True
                break

        if not carved:
            stack.pop()

    return maze


def add_extra_routes(maze: list[list[str]], chance: float = 0.13) -> None:
    """
    Remove selected interior walls to create loops and alternate paths.

    This is important for gameplay: the player can choose between routes
    instead of following one narrow unavoidable corridor.
    """
    rows = len(maze)
    columns = len(maze[0])

    for row in range(1, rows - 1):
        for column in range(1, columns - 1):
            if maze[row][column] != WALL:
                continue

            horizontal_opening = (
                maze[row][column - 1] != WALL
                and maze[row][column + 1] != WALL
            )

            vertical_opening = (
                maze[row - 1][column] != WALL
                and maze[row + 1][column] != WALL
            )

            if (horizontal_opening or vertical_opening) and random.random() < chance:
                maze[row][column] = FLOOR


def walkable_tiles(
    maze: list[list[str]],
    excluded: set[Position] | None = None,
) -> list[Position]:
    """Return all floor positions that are not excluded."""
    excluded = excluded or set()

    tiles = []

    for row, maze_row in enumerate(maze):
        for column, tile in enumerate(maze_row):
            if tile == FLOOR and (row, column) not in excluded:
                tiles.append((row, column))

    return tiles


def choose_far_tile(
    maze: list[list[str]],
    origin: Position,
    candidates: list[Position],
    minimum_distance: int,
) -> Optional[Position]:
    """Choose randomly from candidates sufficiently far from an origin."""
    far_candidates = [
        position
        for position in candidates
        if maze_distance(maze, origin, position) >= minimum_distance
    ]

    if not far_candidates:
        return None

    return random.choice(far_candidates)


def place_tile(
    maze: list[list[str]],
    position: Position,
    symbol: str,
) -> None:
    """Place one special symbol in the maze."""
    row, column = position
    maze[row][column] = symbol


def add_puzzle_items(
    maze: list[list[str]],
    start: Position,
    exit_position: Position,
    key_position: Position,
    enemy_position: Position,
) -> None:
    """
    Add gems, safe zones, switches, and a locked door.

    The puzzle features are placed away from important starting locations.
    They create choices: take a longer route for a safe zone, collect extra
    gems, or activate a switch to slow the BFS hunter.
    """
    reserved = {
        start,
        exit_position,
        key_position,
        enemy_position,
    }

    candidates = walkable_tiles(maze, reserved)
    random.shuffle(candidates)

    # Place energy gems across different parts of the maze.
    gems_placed = 0

    for candidate in candidates:
        if gems_placed >= TOTAL_GEMS:
            break

        far_from_start = maze_distance(maze, start, candidate) >= 7
        far_from_enemy = maze_distance(maze, enemy_position, candidate) >= 4

        if far_from_start and far_from_enemy:
            place_tile(maze, candidate, GEM)
            reserved.add(candidate)
            gems_placed += 1

    # Place two safe zones. These help the player break away from the hunter.
    candidates = walkable_tiles(maze, reserved)
    random.shuffle(candidates)

    safe_zones_placed = 0

    for candidate in candidates:
        if safe_zones_placed >= 2:
            break

        if maze_distance(maze, start, candidate) >= 6:
            place_tile(maze, candidate, SAFE_ZONE)
            reserved.add(candidate)
            safe_zones_placed += 1

    # Place one switch that slows the hunter temporarily.
    candidates = walkable_tiles(maze, reserved)
    random.shuffle(candidates)

    for candidate in candidates:
        if maze_distance(maze, start, candidate) >= 8:
            place_tile(maze, candidate, SWITCH)
            reserved.add(candidate)
            break

    # Place a door near the exit route but not directly on the exit.
    exit_neighbors = valid_neighbors(maze, exit_position, has_key=True)
    random.shuffle(exit_neighbors)

    for neighbor in exit_neighbors:
        if neighbor not in reserved and maze[neighbor[0]][neighbor[1]] == FLOOR:
            place_tile(maze, neighbor, DOOR)
            break


def generate_level() -> GameState:
    """
    Generate a randomized, connected, and reasonably fair puzzle maze.

    The generator retries until it finds a maze where:
    - The key is reachable from the start.
    - The exit is reachable after the key.
    - The enemy begins a meaningful distance away.
    - The start-to-exit route is not too short.
    """
    for _ in range(MAX_GENERATION_ATTEMPTS):
        maze = generate_base_maze(MAZE_ROWS, MAZE_COLS)
        add_extra_routes(maze)

        start = (1, 1)
        place_tile(maze, start, START)

        available = walkable_tiles(maze, {start})
        exit_position = choose_far_tile(
            maze,
            start,
            available,
            MIN_ROUTE_LENGTH,
        )

        if exit_position is None:
            continue

        place_tile(maze, exit_position, EXIT)

        available = walkable_tiles(maze, {start, exit_position})
        key_position = choose_far_tile(
            maze,
            start,
            available,
            12,
        )

        if key_position is None:
            continue

        place_tile(maze, key_position, KEY)

        available = walkable_tiles(maze, {start, exit_position, key_position})
        enemy_position = choose_far_tile(
            maze,
            start,
            available,
            16,
        )

        if enemy_position is None:
            continue

        place_tile(maze, enemy_position, ENEMY)

        key_path = bfs_path(maze, start, key_position, has_key=True)
        exit_path = bfs_path(maze, key_position, exit_position, has_key=True)

        if not key_path or not exit_path:
            continue

        if len(key_path) + len(exit_path) < MIN_ROUTE_LENGTH:
            continue

        add_puzzle_items(
            maze,
            start,
            exit_position,
            key_position,
            enemy_position,
        )

        return GameState(
            maze=maze,
            player=start,
            enemy=enemy_position,
            exit=exit_position,
            key=key_position,
        )

    # Extremely unlikely fallback: regenerate until a usable layout appears.
    return generate_level()


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def draw_gradient(surface: pygame.Surface, width: int, height: int) -> None:
    """Draw a dark blue-to-purple background gradient."""
    for y in range(height):
        ratio = y / max(height - 1, 1)

        red = int(BACKGROUND_TOP[0] * (1 - ratio) + BACKGROUND_BOTTOM[0] * ratio)
        green = int(BACKGROUND_TOP[1] * (1 - ratio) + BACKGROUND_BOTTOM[1] * ratio)
        blue = int(BACKGROUND_TOP[2] * (1 - ratio) + BACKGROUND_BOTTOM[2] * ratio)

        pygame.draw.line(surface, (red, green, blue), (0, y), (width, y))


def draw_centered_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    center: tuple[int, int],
) -> pygame.Rect:
    """Draw centered text and return its screen rectangle."""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center)
    surface.blit(text_surface, text_rect)
    return text_rect


def draw_button(
    surface: pygame.Surface,
    rect: pygame.Rect,
    text: str,
    font: pygame.font.Font,
    mouse_position: tuple[int, int],
) -> None:
    """Draw a rounded button with hover feedback."""
    hovering = rect.collidepoint(mouse_position)

    pygame.draw.rect(surface, SHADOW_COLOR, rect.move(0, 5), border_radius=12)

    color = BUTTON_HOVER_COLOR if hovering else BUTTON_COLOR
    pygame.draw.rect(surface, color, rect, border_radius=12)
    pygame.draw.rect(surface, WHITE, rect, width=2, border_radius=12)

    draw_centered_text(surface, text, font, WHITE, rect.center)


def draw_gem(surface: pygame.Surface, center: tuple[int, int]) -> None:
    """Draw a glowing diamond-shaped energy gem."""
    x, y = center

    points = [
        (x, y - 9),
        (x + 7, y),
        (x, y + 9),
        (x - 7, y),
    ]

    pygame.draw.circle(surface, GEM_GLOW, center, 13)
    pygame.draw.polygon(surface, GEM_COLOR, points)
    pygame.draw.polygon(surface, WHITE, points, width=1)


def draw_key(surface: pygame.Surface, center: tuple[int, int]) -> None:
    """Draw a gold key."""
    x, y = center

    pygame.draw.circle(surface, KEY_COLOR, (x - 4, y - 3), 6)
    pygame.draw.line(surface, KEY_COLOR, (x, y + 1), (x + 10, y + 11), width=4)
    pygame.draw.line(surface, KEY_COLOR, (x + 7, y + 10), (x + 13, y + 10), width=3)


def draw_safe_zone(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Draw a blue safe-zone tile."""
    center = rect.center

    pygame.draw.circle(surface, SAFE_ZONE_GLOW, center, rect.width // 3)
    pygame.draw.circle(surface, SAFE_ZONE_COLOR, center, rect.width // 5)
    pygame.draw.circle(surface, WHITE, center, rect.width // 5, width=1)


def draw_switch(
    surface: pygame.Surface,
    rect: pygame.Rect,
    active: bool = False,
) -> None:
    """Draw a floor switch."""
    color = SWITCH_ACTIVE_COLOR if active else SWITCH_COLOR

    switch_rect = rect.inflate(-10, -12)
    pygame.draw.rect(surface, color, switch_rect, border_radius=4)
    pygame.draw.rect(surface, WHITE, switch_rect, width=1, border_radius=4)


def get_board_layout(
    width: int,
    height: int,
    rows: int,
    columns: int,
) -> tuple[int, int, int]:
    """
    Calculate tile size and board coordinates based on screen size.

    This keeps padding consistent and prevents the board from colliding with
    the header, status panel, and lower buttons.
    """
    available_width = width - 100
    available_height = height - 400

    tile_width = available_width // columns
    tile_height = available_height // rows

    tile_size = max(MIN_TILE_SIZE, min(MAX_TILE_SIZE, tile_width, tile_height))

    maze_width = columns * tile_size
    maze_height = rows * tile_size

    start_x = width // 2 - maze_width // 2
    start_y = 170 + max(0, (available_height - maze_height) // 2)

    return tile_size, start_x, start_y


def draw_maze(
    surface: pygame.Surface,
    game: GameState,
    mouse_position: tuple[int, int],
    width: int,
    height: int,
    button_font: pygame.font.Font,
) -> tuple[pygame.Rect, pygame.Rect]:
    """Draw the maze, puzzle tiles, player, enemy, and bottom buttons."""
    rows = len(game.maze)
    columns = len(game.maze[0])

    tile_size, start_x, start_y = get_board_layout(width, height, rows, columns)

    maze_width = columns * tile_size
    maze_height = rows * tile_size

    panel_padding = 16

    panel_rect = pygame.Rect(
        start_x - panel_padding,
        start_y - panel_padding,
        maze_width + panel_padding * 2,
        maze_height + panel_padding * 2,
    )

    pygame.draw.rect(surface, SHADOW_COLOR, panel_rect.move(0, 8), border_radius=20)
    pygame.draw.rect(surface, PANEL_COLOR, panel_rect, border_radius=20)
    pygame.draw.rect(surface, PANEL_BORDER, panel_rect, width=2, border_radius=20)

    for row, maze_row in enumerate(game.maze):
        for column, tile in enumerate(maze_row):
            rect = pygame.Rect(
                start_x + column * tile_size,
                start_y + row * tile_size,
                tile_size,
                tile_size,
            )

            if tile == WALL:
                pygame.draw.rect(surface, WALL_COLOR, rect, border_radius=4)
                pygame.draw.rect(surface, WALL_EDGE, rect, width=1, border_radius=4)

                highlight_rect = pygame.Rect(
                    rect.x + 3,
                    rect.y + 3,
                    max(2, rect.width - 6),
                    max(2, rect.height // 5),
                )

                pygame.draw.rect(
                    surface,
                    WALL_HIGHLIGHT,
                    highlight_rect,
                    border_radius=3,
                )
            else:
                pygame.draw.rect(surface, FLOOR_COLOR, rect)
                pygame.draw.rect(surface, FLOOR_GRID, rect, width=1)

                if tile == SAFE_ZONE:
                    draw_safe_zone(surface, rect)

                elif tile == SWITCH:
                    draw_switch(surface, rect)

                elif tile == GEM:
                    draw_gem(surface, rect.center)

                elif tile == KEY and not game.has_key:
                    draw_key(surface, rect.center)

                elif tile == DOOR:
                    door_rect = rect.inflate(-5, -3)
                    pygame.draw.rect(
                        surface,
                        DOOR_COLOR,
                        door_rect,
                        border_radius=4,
                    )
                    pygame.draw.rect(
                        surface,
                        DOOR_EDGE,
                        door_rect,
                        width=1,
                        border_radius=4,
                    )

                elif tile == EXIT:
                    exit_color = (
                        EXIT_OPEN_COLOR
                        if game.has_key and game.gems_collected >= game.gems_required
                        else EXIT_LOCKED_COLOR
                    )

                    exit_rect = rect.inflate(-6, -6)
                    pygame.draw.rect(
                        surface,
                        exit_color,
                        exit_rect,
                        border_radius=5,
                    )

                    pygame.draw.rect(
                        surface,
                        WHITE,
                        exit_rect,
                        width=1,
                        border_radius=5,
                    )

    player_row, player_col = game.player
    player_center = (
        start_x + player_col * tile_size + tile_size // 2,
        start_y + player_row * tile_size + tile_size // 2,
    )

    player_radius = max(6, tile_size // 4)
    pygame.draw.circle(surface, PLAYER_GLOW, player_center, player_radius + 5)
    pygame.draw.circle(surface, PLAYER_COLOR, player_center, player_radius)
    pygame.draw.circle(surface, WHITE, player_center, player_radius, width=1)

    enemy_row, enemy_col = game.enemy
    enemy_center = (
        start_x + enemy_col * tile_size + tile_size // 2,
        start_y + enemy_row * tile_size + tile_size // 2,
    )

    enemy_radius = max(6, tile_size // 4)
    pulse_radius = enemy_radius + 5 + min(game.enemy_pulse, 7)

    pygame.draw.circle(surface, ENEMY_GLOW, enemy_center, pulse_radius)
    pygame.draw.circle(surface, ENEMY_COLOR, enemy_center, enemy_radius)
    pygame.draw.circle(surface, WHITE, enemy_center, enemy_radius, width=1)

    back_button = pygame.Rect(30, height - 62, 165, 40)
    restart_button = pygame.Rect(width - 195, height - 62, 165, 40)

    draw_button(surface, back_button, "Main Menu", button_font, mouse_position)
    draw_button(surface, restart_button, "New Maze", button_font, mouse_position)

    return back_button, restart_button


def draw_hud(
    surface: pygame.Surface,
    game: GameState,
    small_font: pygame.font.Font,
    medium_font: pygame.font.Font,
    large_font: pygame.font.Font,
    width: int,
    height: int,
) -> None:
    """Draw the title, current objective, and puzzle progress."""
    draw_centered_text(
        surface,
        "MAZE ESCAPE",
        large_font,
        WHITE,
        (width // 2, 31),
    )

    draw_centered_text(
        surface,
        "Randomized BFS Hunter Challenge",
        small_font,
        TEXT_MUTED,
        (width // 2, 63),
    )

    status_rect = pygame.Rect(width // 2 - 335, 80, 670, 38)

    pygame.draw.rect(surface, PANEL_COLOR, status_rect, border_radius=10)
    pygame.draw.rect(surface, PANEL_BORDER, status_rect, width=1, border_radius=10)

    if game.game_over:
        if game.won:
            message = f"Escape successful in {game.moves} moves!"
            color = EXIT_OPEN_COLOR
        else:
            message = "The BFS hunter caught you. Press R for a new maze."
            color = ENEMY_COLOR

    elif not game.has_key:
        message = "Find the gold key. Blue zones protect you briefly."
        color = WHITE

    elif game.gems_collected < game.gems_required:
        message = "Key found! Collect enough cyan energy gems."
        color = GEM_COLOR

    else:
        message = "Exit unlocked! Reach the green exit."
        color = EXIT_OPEN_COLOR

    draw_centered_text(surface, message, small_font, color, status_rect.center)

    progress_text = (
        f"Moves: {game.moves}     "
        f"Key: {'YES' if game.has_key else 'NO'}     "
        f"Gems: {game.gems_collected}/{game.gems_required}"
    )

    draw_centered_text(
        surface,
        progress_text,
        medium_font,
        WHITE,
        (width // 2, height - 93),
    )

    if game.enemy_slow_turns > 0:
        effect_text = f"Switch active: Hunter slowed for {game.enemy_slow_turns} turns"
        effect_color = SWITCH_ACTIVE_COLOR

    elif game.safe_turns > 0:
        effect_text = f"Safe zone active: Hunter paused for {game.safe_turns} turn(s)"
        effect_color = SAFE_ZONE_GLOW

    else:
        effect_text = (
            f"Hunter moves every {ENEMY_MOVES_EVERY} player moves"
        )
        effect_color = TEXT_MUTED

    draw_centered_text(
        surface,
        effect_text,
        small_font,
        effect_color,
        (width // 2, height - 72),
    )

    draw_centered_text(
        surface,
        "Move: Arrow Keys / WASD     New Maze: R     Exit: ESC",
        small_font,
        TEXT_MUTED,
        (width // 2, height - 41),
    )


# ---------------------------------------------------------------------------
# Gameplay logic
# ---------------------------------------------------------------------------

def update_tile_effects(game: GameState) -> None:
    """Apply the effect of the tile currently occupied by the player."""
    row, column = game.player
    tile = game.maze[row][column]

    if tile == KEY:
        game.has_key = True
        game.maze[row][column] = FLOOR
        game.message = "Key acquired! Locked doors can now be opened."
        game.message_color = KEY_COLOR

    elif tile == GEM:
        game.gems_collected += 1
        game.maze[row][column] = FLOOR
        game.message = f"Energy gem collected: {game.gems_collected}/{game.gems_required}"
        game.message_color = GEM_COLOR

    elif tile == SAFE_ZONE:
        game.safe_turns = SAFE_ZONE_PROTECTION_TURNS
        game.message = "Safe zone activated. The hunter is paused."
        game.message_color = SAFE_ZONE_GLOW

    elif tile == SWITCH:
        game.enemy_slow_turns = SWITCH_SLOWDOWN_TURNS
        game.maze[row][column] = FLOOR
        game.message = "Switch activated. The hunter has been slowed."
        game.message_color = SWITCH_ACTIVE_COLOR


def enemy_should_move(game: GameState) -> bool:
    """Return True when the BFS hunter should make a move this turn."""
    if game.moves % ENEMY_MOVES_EVERY != 0:
        return False

    if game.safe_turns > 0:
        game.safe_turns -= 1
        return False

    if game.enemy_slow_turns > 0:
        game.enemy_slow_turns -= 1

        # During slowdown, the hunter moves only every second eligible turn.
        return game.enemy_slow_turns % 2 == 0

    return True


def try_move_player(game: GameState, direction: Position) -> None:
    """Try to move the player and resolve all game effects."""
    if game.game_over:
        return

    player_row, player_col = game.player

    next_position = (
        player_row + direction[0],
        player_col + direction[1],
    )

    if not is_walkable(game.maze, next_position, game.has_key):
        return

    game.player = next_position
    game.moves += 1

    update_tile_effects(game)

    if game.player == game.exit:
        if not game.has_key:
            game.message = "The exit is locked. You need the gold key."
            game.message_color = WARNING_COLOR

        elif game.gems_collected < game.gems_required:
            needed = game.gems_required - game.gems_collected
            game.message = f"Exit needs {needed} more energy gem(s)."
            game.message_color = WARNING_COLOR

        else:
            game.game_over = True
            game.won = True
            return

    if enemy_should_move(game):
        game.enemy = bfs_next_step(
            game.maze,
            game.enemy,
            game.player,
        )
        game.enemy_pulse = 8

    if game.enemy == game.player:
        game.game_over = True
        game.won = False


def key_to_direction(key: int) -> Optional[Position]:
    """Convert keyboard movement input into a grid direction."""
    directions = {
        pygame.K_UP: (-1, 0),
        pygame.K_w: (-1, 0),
        pygame.K_DOWN: (1, 0),
        pygame.K_s: (1, 0),
        pygame.K_LEFT: (0, -1),
        pygame.K_a: (0, -1),
        pygame.K_RIGHT: (0, 1),
        pygame.K_d: (0, 1),
    }

    return directions.get(key)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """
    Run Maze Escape.

    Returns:
        "menu" when the player chooses to return to the main menu.
    """
    width, height = screen.get_size()

    try:
        small_font = pygame.font.Font("OpenSans-Regular.ttf", 18)
        medium_font = pygame.font.Font("OpenSans-Regular.ttf", 21)
        large_font = pygame.font.Font("OpenSans-Regular.ttf", 38)
        button_font = pygame.font.Font("OpenSans-Regular.ttf", 18)
    except FileNotFoundError:
        small_font = pygame.font.SysFont("arial", 18)
        medium_font = pygame.font.SysFont("arial", 21, bold=True)
        large_font = pygame.font.SysFont("arial", 38, bold=True)
        button_font = pygame.font.SysFont("arial", 18, bold=True)

    game = generate_level()

    back_button = pygame.Rect(0, 0, 0, 0)
    restart_button = pygame.Rect(0, 0, 0, 0)

    while True:
        mouse_position = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"

                if event.key == pygame.K_r:
                    game = generate_level()
                    continue

                direction = key_to_direction(event.key)

                if direction is not None:
                    try_move_player(game, direction)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.collidepoint(event.pos):
                    return "menu"

                if restart_button.collidepoint(event.pos):
                    game = generate_level()

        if game.enemy_pulse > 0:
            game.enemy_pulse -= 1

        draw_gradient(screen, width, height)

        draw_hud(
            screen,
            game,
            small_font,
            medium_font,
            large_font,
            width,
            height,
        )

        back_button, restart_button = draw_maze(
            screen,
            game,
            mouse_position,
            width,
            height,
            button_font,
        )

        pygame.display.flip()
        clock.tick(60)