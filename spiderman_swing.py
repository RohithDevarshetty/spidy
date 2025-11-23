#!/usr/bin/env python3
"""
Spiderman Swinging Game - A Terminal-Based Adventure
Swing through the city, avoid obstacles, and rack up points!
"""

import curses
import random
import math
import time
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

# Game Constants
GRAVITY = 0.5
SWING_STRENGTH = 1.5
MAX_ROPE_LENGTH = 20
MIN_BUILDING_HEIGHT = 10
MAX_BUILDING_HEIGHT = 30
BUILDING_WIDTH = 8
GAME_SPEED = 0.05


class GameState(Enum):
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2


@dataclass
class Building:
    x: int
    height: int
    width: int = BUILDING_WIDTH
    has_obstacle: bool = False
    obstacle_height: int = 0


@dataclass
class SpiderMan:
    x: float
    y: float
    vx: float = 0
    vy: float = 0
    rope_length: float = 0
    rope_angle: float = 0
    is_swinging: bool = False
    swing_anchor_x: float = 0
    swing_anchor_y: float = 0


class SpidermanGame:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        self.state = GameState.MENU
        self.score = 0
        self.high_score = 0

        # Initialize curses
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(1)   # Non-blocking input
        stdscr.timeout(50)  # 50ms timeout

        # Initialize colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)      # Spiderman
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)     # Buildings
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_CYAN)      # Building fill
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)   # Web
        curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)    # Score
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Obstacles
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLUE)     # Sky

        self.spiderman = None
        self.buildings: List[Building] = []
        self.camera_x = 0

    def init_game(self):
        """Initialize a new game"""
        self.state = GameState.PLAYING
        self.score = 0
        start_x = 20
        start_y = self.height - 15

        self.spiderman = SpiderMan(x=start_x, y=start_y)
        self.buildings = []
        self.camera_x = 0

        # Generate initial buildings
        for i in range(10):
            self.buildings.append(self.generate_building(i * 20))

    def generate_building(self, base_x: int) -> Building:
        """Generate a random building"""
        height = random.randint(MIN_BUILDING_HEIGHT, MAX_BUILDING_HEIGHT)
        has_obstacle = random.random() < 0.3  # 30% chance of obstacle
        obstacle_height = random.randint(5, height - 5) if has_obstacle and height > 10 else 0

        return Building(
            x=base_x,
            height=height,
            has_obstacle=has_obstacle,
            obstacle_height=obstacle_height
        )

    def update_buildings(self):
        """Update buildings and generate new ones"""
        # Remove buildings that are off-screen to the left
        self.buildings = [b for b in self.buildings if b.x + b.width > self.camera_x - 10]

        # Add new buildings to the right
        if self.buildings:
            last_building = max(self.buildings, key=lambda b: b.x)
            while last_building.x < self.camera_x + self.width + 50:
                new_x = last_building.x + random.randint(15, 30)
                self.buildings.append(self.generate_building(new_x))
                last_building = self.buildings[-1]

    def handle_input(self, key):
        """Handle keyboard input"""
        if self.state == GameState.MENU:
            if key in [ord('s'), ord('S'), ord(' ')]:
                self.init_game()

        elif self.state == GameState.PLAYING:
            if key == ord(' '):
                self.shoot_web()
            elif key == ord('q'):
                self.state = GameState.GAME_OVER

        elif self.state == GameState.GAME_OVER:
            if key in [ord('r'), ord('R')]:
                self.init_game()
            elif key == ord('q'):
                return False

        return True

    def shoot_web(self):
        """Shoot web to the nearest building anchor point"""
        if not self.spiderman.is_swinging:
            # Find the nearest building top ahead
            nearest = None
            min_distance = float('inf')

            for building in self.buildings:
                bldg_top_x = building.x + building.width // 2
                bldg_top_y = self.height - building.height - 1

                # Only consider buildings ahead and above
                if bldg_top_x > self.spiderman.x:
                    distance = math.sqrt(
                        (bldg_top_x - self.spiderman.x) ** 2 +
                        (bldg_top_y - self.spiderman.y) ** 2
                    )

                    if distance < MAX_ROPE_LENGTH and distance < min_distance:
                        min_distance = distance
                        nearest = (bldg_top_x, bldg_top_y)

            if nearest:
                self.spiderman.is_swinging = True
                self.spiderman.swing_anchor_x = nearest[0]
                self.spiderman.swing_anchor_y = nearest[1]
                self.spiderman.rope_length = min_distance

    def update_physics(self):
        """Update game physics"""
        if self.state != GameState.PLAYING:
            return

        spidy = self.spiderman

        if spidy.is_swinging:
            # Calculate rope angle and tension
            dx = spidy.x - spidy.swing_anchor_x
            dy = spidy.y - spidy.swing_anchor_y
            current_distance = math.sqrt(dx**2 + dy**2)

            if current_distance > spidy.rope_length:
                # Apply constraint - keep spiderman on the circle
                angle = math.atan2(dy, dx)
                spidy.x = spidy.swing_anchor_x + spidy.rope_length * math.cos(angle)
                spidy.y = spidy.swing_anchor_y + spidy.rope_length * math.sin(angle)

                # Apply swing physics
                tangent_vx = -math.sin(angle)
                tangent_vy = math.cos(angle)

                # Project velocity onto tangent
                v_tangent = spidy.vx * tangent_vx + spidy.vy * tangent_vy

                # Apply gravity component along tangent
                gravity_tangent = GRAVITY * math.cos(angle)
                v_tangent += gravity_tangent

                # Update velocity
                spidy.vx = v_tangent * tangent_vx
                spidy.vy = v_tangent * tangent_vy

            # Release web if moving upward and rope is taut
            if spidy.vy < -2:
                spidy.is_swinging = False

        else:
            # Free fall physics
            spidy.vy += GRAVITY
            spidy.vx *= 0.99  # Air resistance

        # Apply velocity
        spidy.x += spidy.vx
        spidy.y += spidy.vy

        # Update camera to follow spiderman
        target_camera_x = spidy.x - self.width // 3
        self.camera_x += (target_camera_x - self.camera_x) * 0.1

        # Check collisions
        self.check_collisions()

        # Update score
        self.score = max(self.score, int(spidy.x // 10))

        # Update buildings
        self.update_buildings()

    def check_collisions(self):
        """Check for collisions with buildings and obstacles"""
        spidy = self.spiderman
        ground_level = self.height - 1

        # Check ground collision
        if spidy.y >= ground_level:
            self.state = GameState.GAME_OVER
            self.high_score = max(self.high_score, self.score)
            return

        # Check building collisions
        for building in self.buildings:
            bldg_top = self.height - building.height
            bldg_left = building.x
            bldg_right = building.x + building.width

            # Check if spiderman is within building bounds
            if (bldg_left <= spidy.x <= bldg_right and
                spidy.y >= bldg_top):

                # Check if hit obstacle
                if building.has_obstacle:
                    obstacle_y = self.height - building.obstacle_height
                    if abs(spidy.y - obstacle_y) < 2:
                        self.state = GameState.GAME_OVER
                        self.high_score = max(self.high_score, self.score)
                        return

    def draw_menu(self):
        """Draw the main menu"""
        self.stdscr.clear()

        title = [
            "  _____ ____ _____ ____  _____ ____  __  __    _    _   _",
            " / ____|  _ \\_   _|  _ \\| ____|  _ \\|  \\/  |  / \\  | \\ | |",
            " \\___ \\| |_) || | | | | |  _| | |_) | |\\/| | / _ \\ |  \\| |",
            "  ___) |  __/ | | | |_| | |___|  _ <| |  | |/ ___ \\| |\\  |",
            " |____/|_|   |_| |____/|_____|_| \\_\\_|  |_/_/   \\_\\_| \\_|",
            "",
            "                    SWING THROUGH THE CITY!",
        ]

        start_y = self.height // 2 - len(title) - 5

        for i, line in enumerate(title):
            if start_y + i < self.height:
                x = max(0, (self.width - len(line)) // 2)
                try:
                    self.stdscr.addstr(start_y + i, x, line, curses.color_pair(1) | curses.A_BOLD)
                except:
                    pass

        instructions = [
            "",
            "Controls:",
            "  [SPACE] - Shoot Web / Swing",
            "  [Q]     - Quit",
            "",
            "Objective: Swing through the city without hitting the ground!",
            "",
            "Press [SPACE] to start!",
        ]

        for i, line in enumerate(instructions):
            y = start_y + len(title) + i + 2
            if y < self.height:
                x = max(0, (self.width - len(line)) // 2)
                try:
                    color = curses.color_pair(5) if "Press" in line else curses.color_pair(0)
                    self.stdscr.addstr(y, x, line, color)
                except:
                    pass

        if self.high_score > 0:
            score_text = f"High Score: {self.high_score}"
            try:
                self.stdscr.addstr(self.height - 3, (self.width - len(score_text)) // 2,
                                 score_text, curses.color_pair(5) | curses.A_BOLD)
            except:
                pass

    def draw_game_over(self):
        """Draw game over screen"""
        self.stdscr.clear()

        game_over_text = [
            "  ____    _    __  __ _____    _____     _______ ____  ",
            " / ___|  / \\  |  \\/  | ____|  / _ \\ \\   / / ____|  _ \\ ",
            "| |  _  / _ \\ | |\\/| |  _|   | | | \\ \\ / /|  _| | |_) |",
            "| |_| |/ ___ \\| |  | | |___  | |_| |\\ V / | |___|  _ < ",
            " \\____/_/   \\_\\_|  |_|_____|  \\___/  \\_/  |_____|_| \\_\\",
        ]

        start_y = self.height // 2 - 8

        for i, line in enumerate(game_over_text):
            if start_y + i < self.height:
                x = max(0, (self.width - len(line)) // 2)
                try:
                    self.stdscr.addstr(start_y + i, x, line, curses.color_pair(1) | curses.A_BOLD)
                except:
                    pass

        score_text = f"Final Score: {self.score}"
        high_score_text = f"High Score: {self.high_score}"

        try:
            self.stdscr.addstr(start_y + 7, (self.width - len(score_text)) // 2,
                             score_text, curses.color_pair(5) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 8, (self.width - len(high_score_text)) // 2,
                             high_score_text, curses.color_pair(5) | curses.A_BOLD)
        except:
            pass

        restart_text = "[R] Restart    [Q] Quit"
        try:
            self.stdscr.addstr(start_y + 11, (self.width - len(restart_text)) // 2,
                             restart_text, curses.color_pair(0))
        except:
            pass

    def draw_game(self):
        """Draw the game state"""
        self.stdscr.clear()

        # Draw sky/background
        for y in range(self.height - 1):
            try:
                self.stdscr.addstr(y, 0, ' ' * self.width, curses.color_pair(0))
            except:
                pass

        # Draw buildings
        for building in self.buildings:
            screen_x = int(building.x - self.camera_x)

            if -building.width <= screen_x <= self.width:
                bldg_top = self.height - building.height

                # Draw building
                for y in range(bldg_top, self.height):
                    for x in range(building.width):
                        draw_x = screen_x + x
                        if 0 <= draw_x < self.width and 0 <= y < self.height:
                            # Building pattern
                            if (x == 0 or x == building.width - 1 or
                                y == bldg_top):
                                char = '█'
                                color = curses.color_pair(2) | curses.A_BOLD
                            elif (x % 3 == 1 and y % 3 == 1):
                                char = '▓'
                                color = curses.color_pair(3)
                            else:
                                char = '░'
                                color = curses.color_pair(3)

                            try:
                                self.stdscr.addstr(y, draw_x, char, color)
                            except:
                                pass

                # Draw obstacle
                if building.has_obstacle:
                    obstacle_y = self.height - building.obstacle_height
                    for x in range(building.width):
                        draw_x = screen_x + x
                        if 0 <= draw_x < self.width and 0 <= obstacle_y < self.height:
                            try:
                                self.stdscr.addstr(obstacle_y, draw_x, '▼',
                                                 curses.color_pair(6) | curses.A_BOLD)
                            except:
                                pass

        # Draw web rope
        if self.spiderman.is_swinging:
            rope_x = int(self.spiderman.swing_anchor_x - self.camera_x)
            rope_y = int(self.spiderman.swing_anchor_y)
            spidy_x = int(self.spiderman.x - self.camera_x)
            spidy_y = int(self.spiderman.y)

            # Draw line from anchor to spiderman
            steps = max(abs(rope_x - spidy_x), abs(rope_y - spidy_y))
            if steps > 0:
                for i in range(steps):
                    t = i / steps
                    x = int(rope_x + (spidy_x - rope_x) * t)
                    y = int(rope_y + (spidy_y - rope_y) * t)

                    if 0 <= x < self.width and 0 <= y < self.height:
                        char = '/' if i % 2 == 0 else '\\'
                        try:
                            self.stdscr.addstr(y, x, char, curses.color_pair(4))
                        except:
                            pass

        # Draw Spiderman
        spidy_screen_x = int(self.spiderman.x - self.camera_x)
        spidy_screen_y = int(self.spiderman.y)

        if 0 <= spidy_screen_x < self.width and 0 <= spidy_screen_y < self.height:
            # Spiderman character with style
            spidy_char = '⚡' if self.spiderman.is_swinging else '●'
            try:
                self.stdscr.addstr(spidy_screen_y, spidy_screen_x, spidy_char,
                                 curses.color_pair(1) | curses.A_BOLD)
            except:
                pass

        # Draw HUD
        score_text = f"Score: {self.score}"
        speed_text = f"Speed: {abs(self.spiderman.vx):.1f}"

        try:
            self.stdscr.addstr(1, 2, score_text, curses.color_pair(5) | curses.A_BOLD)
            self.stdscr.addstr(2, 2, speed_text, curses.color_pair(5))
            self.stdscr.addstr(0, self.width - 20, "[SPACE] Swing [Q] Quit",
                             curses.color_pair(0))
        except:
            pass

    def run(self):
        """Main game loop"""
        while True:
            # Handle input
            try:
                key = self.stdscr.getch()
            except:
                key = -1

            if key != -1:
                if not self.handle_input(key):
                    break

            # Update game state
            if self.state == GameState.PLAYING:
                self.update_physics()

            # Draw
            if self.state == GameState.MENU:
                self.draw_menu()
            elif self.state == GameState.PLAYING:
                self.draw_game()
            elif self.state == GameState.GAME_OVER:
                self.draw_game_over()

            self.stdscr.refresh()
            time.sleep(GAME_SPEED)


def main(stdscr):
    """Main entry point"""
    game = SpidermanGame(stdscr)
    game.run()


def main_wrapper():
    """Wrapper for console script entry point"""
    import sys

    # Handle version flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--version', '-v']:
        print("Spidy - Spiderman Swinging Game v1.0.0")
        print("A terminal-based adventure game")
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("Spidy - Spiderman Swinging Game")
        print("\nUsage: spidy")
        print("\nControls:")
        print("  SPACE - Shoot web and swing")
        print("  Q     - Quit game")
        print("\nObjective: Swing through the city without hitting the ground!")
        print("\nFor the best experience, maximize your terminal window.")
        sys.exit(0)

    curses.wrapper(main)


if __name__ == "__main__":
    main_wrapper()
