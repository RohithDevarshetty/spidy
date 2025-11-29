#!/usr/bin/env python3
"""
Penalty Shootout - A Terminal-Based Football Game
Experience the thrill of penalty kicks as both shooter and goalkeeper!
"""

import curses
import random
import time
import os
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum


class GameMode(Enum):
    MENU = 0
    SHOOTER = 1
    GOALKEEPER = 2
    TOURNAMENT = 3
    REPLAY = 4


class Zone(Enum):
    """9 zones of the goal"""
    TOP_LEFT = 0
    TOP_CENTER = 1
    TOP_RIGHT = 2
    MID_LEFT = 3
    MID_CENTER = 4
    MID_RIGHT = 5
    BOTTOM_LEFT = 6
    BOTTOM_CENTER = 7
    BOTTOM_RIGHT = 8


@dataclass
class Ball:
    x: float
    y: float
    vx: float = 0
    vy: float = 0
    spinning: bool = False


@dataclass
class Player:
    x: float
    y: float
    is_diving: bool = False
    dive_direction: str = "center"  # "left", "right", "center"
    dive_progress: float = 0.0
    hand_used: str = "both"  # "left", "right", "both"


@dataclass
class Shot:
    zone: Zone
    power: float  # 0.0 to 1.0
    accuracy: float  # Affected by power and pressure
    is_chip: bool = False


class PenaltyShootout:
    def __init__(self, stdscr):
        self.stdscr = stdscr

        if not self._check_terminal():
            raise RuntimeError("Terminal does not support required features")

        self.height, self.width = stdscr.getmaxyx()
        self.mode = GameMode.MENU

        # Game state
        self.score_player = 0
        self.score_opponent = 0
        self.round_num = 1
        self.max_rounds = 5
        self.is_player_turn_to_shoot = True

        # Shooter state
        self.selected_zone = Zone.MID_CENTER
        self.power_level = 0.0
        self.is_charging_power = False
        self.space_was_held = False  # Track if SPACE was held last frame
        self.pressure = 0.3  # Increases each round

        # Goalkeeper state
        self.goalkeeper = Player(x=self.width // 2, y=self.height - 15)
        self.ball = None
        self.shot_taken = False
        self.result_message = ""
        self.result_timer = 0

        # Animation state
        self.frame_count = 0
        self.animation_phase = 0  # For various animations

        # Statistics
        self.shots_taken = 0
        self.goals_scored = 0
        self.saves_made = 0
        self.perfect_shots = 0  # Goals in corners with high power

        # Initialize curses
        curses.curs_set(0)
        stdscr.nodelay(1)
        stdscr.timeout(30)

        try:
            curses.use_default_colors()
        except:
            pass

        self._init_colors()

    def _check_terminal(self) -> bool:
        try:
            if 'TERM' not in os.environ or os.environ['TERM'] == 'unknown':
                os.environ['TERM'] = 'xterm-256color'
            return True
        except:
            return False

    def _init_colors(self):
        curses.start_color()

        try:
            if curses.COLORS >= 256:
                curses.init_pair(1, 46, -1)     # Green - Grass/Success
                curses.init_pair(2, 226, -1)    # Yellow - Ball
                curses.init_pair(3, 21, -1)     # Blue - Player
                curses.init_pair(4, 196, -1)    # Red - Goalkeeper/Fail
                curses.init_pair(5, 15, -1)     # White - Goal
                curses.init_pair(6, 240, -1)    # Gray - UI
                curses.init_pair(7, 202, -1)    # Orange - Power
                curses.init_pair(8, 51, -1)     # Cyan - Effects
            else:
                raise Exception("Fallback")
        except:
            curses.init_pair(1, curses.COLOR_GREEN, -1)
            curses.init_pair(2, curses.COLOR_YELLOW, -1)
            curses.init_pair(3, curses.COLOR_BLUE, -1)
            curses.init_pair(4, curses.COLOR_RED, -1)
            curses.init_pair(5, curses.COLOR_WHITE, -1)
            curses.init_pair(6, curses.COLOR_WHITE, -1)
            curses.init_pair(7, curses.COLOR_YELLOW, -1)
            curses.init_pair(8, curses.COLOR_CYAN, -1)

    def init_shooter_mode(self):
        """Initialize shooter mode"""
        self.mode = GameMode.SHOOTER
        self.selected_zone = Zone.MID_CENTER
        self.power_level = 0.0
        self.is_charging_power = False
        self.space_was_held = False
        self.shot_taken = False
        self.ball = None
        self.goalkeeper.is_diving = False
        self.goalkeeper.dive_progress = 0.0
        self.result_message = ""
        self.result_timer = 0

    def init_goalkeeper_mode(self):
        """Initialize goalkeeper mode"""
        self.mode = GameMode.GOALKEEPER
        self.shot_taken = False
        self.ball = None
        self.goalkeeper.is_diving = False
        self.goalkeeper.dive_progress = 0.0
        self.result_message = ""
        self.result_timer = 0

        # AI opponent takes a shot
        self.ai_shot_zone = random.choice(list(Zone))
        self.ai_shot_power = random.uniform(0.5, 1.0)
        self.ai_shot_delay = 60  # Frames before AI shoots

    def handle_input(self, key):
        """Handle keyboard input"""
        if self.mode == GameMode.MENU:
            if key == ord('1'):
                self.init_shooter_mode()
            elif key == ord('2'):
                self.init_goalkeeper_mode()
            elif key == ord('3'):
                self.start_tournament()
            elif key == ord('q'):
                return False

        elif self.mode == GameMode.SHOOTER:
            if not self.shot_taken:
                # Zone selection
                if key == curses.KEY_LEFT:
                    self.move_zone_selection(-1, 0)
                elif key == curses.KEY_RIGHT:
                    self.move_zone_selection(1, 0)
                elif key == curses.KEY_UP:
                    self.move_zone_selection(0, -1)
                elif key == curses.KEY_DOWN:
                    self.move_zone_selection(0, 1)

                # Power charging - SPACE key
                if key == ord(' '):
                    # SPACE is being held
                    if not self.is_charging_power:
                        self.is_charging_power = True
                        self.power_level = 0.0
                    self.space_was_held = True
                else:
                    # SPACE was released - shoot!
                    if self.space_was_held and self.is_charging_power:
                        self.is_charging_power = False
                        self.take_shot(is_chip=False)
                    self.space_was_held = False

                # Special shots
                if key in [ord('c'), ord('C')]:
                    # Chip shot
                    self.take_shot(is_chip=True)

            # Return to menu
            if key == ord('q'):
                self.mode = GameMode.MENU

            # Next round after result shown
            if self.result_timer > 0 and key == ord(' ') and not self.space_was_held:
                self.init_shooter_mode()

        elif self.mode == GameMode.GOALKEEPER:
            if not self.shot_taken and self.ai_shot_delay <= 0:
                # Dive controls
                if key in [ord('a'), ord('A')]:
                    self.dive_goalkeeper("left", "left")
                elif key in [ord('d'), ord('D')]:
                    self.dive_goalkeeper("right", "right")
                elif key in [ord('s'), ord('S')]:
                    self.dive_goalkeeper("center", "both")

                # Two-hand combinations
                elif key in [ord('w'), ord('W')]:
                    self.dive_goalkeeper("center", "both")  # Jump up with both hands

            if key == ord('q'):
                self.mode = GameMode.MENU

            if self.result_timer > 0 and key == ord(' '):
                self.init_goalkeeper_mode()

        return True

    def move_zone_selection(self, dx: int, dy: int):
        """Move the zone selection cursor"""
        zones_grid = [
            [Zone.TOP_LEFT, Zone.TOP_CENTER, Zone.TOP_RIGHT],
            [Zone.MID_LEFT, Zone.MID_CENTER, Zone.MID_RIGHT],
            [Zone.BOTTOM_LEFT, Zone.BOTTOM_CENTER, Zone.BOTTOM_RIGHT]
        ]

        # Find current position
        for row_idx, row in enumerate(zones_grid):
            if self.selected_zone in row:
                col_idx = row.index(self.selected_zone)

                # Move
                new_row = max(0, min(2, row_idx + dy))
                new_col = max(0, min(2, col_idx + dx))

                self.selected_zone = zones_grid[new_row][new_col]
                break

    def take_shot(self, is_chip: bool = False):
        """Execute the shot"""
        self.shot_taken = True
        self.shots_taken += 1

        # Calculate accuracy based on power and pressure
        accuracy = 1.0 - (self.power_level * 0.3) - (self.pressure * 0.2)
        accuracy = max(0.3, min(1.0, accuracy + random.uniform(-0.1, 0.1)))

        # Create ball
        goal_positions = self.get_zone_position(self.selected_zone)

        # Add randomness based on accuracy
        inaccuracy_x = random.uniform(-5, 5) * (1.0 - accuracy)
        inaccuracy_y = random.uniform(-3, 3) * (1.0 - accuracy)

        target_x = goal_positions[0] + inaccuracy_x
        target_y = goal_positions[1] + inaccuracy_y

        # Start position
        start_x = self.width // 2
        start_y = self.height - 5

        self.ball = Ball(x=start_x, y=start_y)

        # Calculate velocity
        distance = ((target_x - start_x)**2 + (target_y - start_y)**2)**0.5
        speed = 0.5 + (self.power_level * 1.5)

        if distance > 0:
            self.ball.vx = (target_x - start_x) / distance * speed
            self.ball.vy = (target_y - start_y) / distance * speed

        self.ball.spinning = is_chip

        # AI goalkeeper tries to save
        self.ai_goalkeeper_dive()

    def ai_goalkeeper_dive(self):
        """AI goalkeeper attempts to save"""
        # Determine if goalkeeper dives correctly
        zone_col = self.selected_zone.value % 3

        # AI has chance to guess right based on difficulty
        ai_skill = 0.4 + (self.round_num * 0.05)  # Gets better each round

        if random.random() < ai_skill:
            # Correct dive
            if zone_col == 0:
                self.goalkeeper.dive_direction = "left"
                self.goalkeeper.hand_used = "left"
            elif zone_col == 2:
                self.goalkeeper.dive_direction = "right"
                self.goalkeeper.hand_used = "right"
            else:
                self.goalkeeper.dive_direction = "center"
                self.goalkeeper.hand_used = "both"
        else:
            # Random dive
            self.goalkeeper.dive_direction = random.choice(["left", "center", "right"])
            self.goalkeeper.hand_used = random.choice(["left", "right", "both"])

        self.goalkeeper.is_diving = True

    def dive_goalkeeper(self, direction: str, hand: str):
        """Player dives as goalkeeper"""
        self.goalkeeper.dive_direction = direction
        self.goalkeeper.hand_used = hand
        self.goalkeeper.is_diving = True
        self.shot_taken = True

    def start_tournament(self):
        """Start tournament mode"""
        self.mode = GameMode.TOURNAMENT
        self.score_player = 0
        self.score_opponent = 0
        self.round_num = 1
        self.is_player_turn_to_shoot = True
        self.init_shooter_mode()

    def get_zone_position(self, zone: Zone) -> Tuple[int, int]:
        """Get screen position for a goal zone"""
        goal_left = self.width // 2 - 25
        goal_right = self.width // 2 + 25
        goal_top = 5
        goal_bottom = 18

        zone_col = zone.value % 3
        zone_row = zone.value // 3

        x_positions = [goal_left + 8, (goal_left + goal_right) // 2, goal_right - 8]
        y_positions = [goal_top + 3, (goal_top + goal_bottom) // 2, goal_bottom - 3]

        return (x_positions[zone_col], y_positions[zone_row])

    def update_physics(self):
        """Update game physics"""
        self.frame_count += 1

        if self.mode == GameMode.SHOOTER:
            # Power charging
            if self.is_charging_power and not self.shot_taken:
                self.power_level += 0.02
                if self.power_level >= 1.0:
                    self.power_level = 1.0  # Cap at 100%, wait for release

            # Ball movement
            if self.ball:
                self.ball.x += self.ball.vx
                self.ball.y += self.ball.vy

                # Check if ball reached goal or out
                if self.ball.y <= 3 or abs(self.ball.x - self.width // 2) > 30:
                    self.check_goal()

            # Goalkeeper animation
            if self.goalkeeper.is_diving:
                self.goalkeeper.dive_progress = min(1.0, self.goalkeeper.dive_progress + 0.1)

        elif self.mode == GameMode.GOALKEEPER:
            # AI shot countdown
            if self.ai_shot_delay > 0:
                self.ai_shot_delay -= 1
            elif self.ai_shot_delay == 0 and not self.shot_taken:
                # AI shoots
                self.ai_take_shot()
                self.ai_shot_delay = -1

            # Ball movement
            if self.ball:
                self.ball.x += self.ball.vx
                self.ball.y += self.ball.vy

                if self.ball.y >= self.height - 20:
                    self.check_save()

            # Goalkeeper animation
            if self.goalkeeper.is_diving:
                self.goalkeeper.dive_progress = min(1.0, self.goalkeeper.dive_progress + 0.15)

        # Result timer
        if self.result_timer > 0:
            self.result_timer -= 1

    def ai_take_shot(self):
        """AI opponent takes a shot"""
        goal_positions = self.get_zone_position(self.ai_shot_zone)

        # Add some randomness
        accuracy = 0.7 + random.uniform(0, 0.2)
        target_x = goal_positions[0] + random.uniform(-5, 5) * (1.0 - accuracy)
        target_y = goal_positions[1] + random.uniform(-3, 3) * (1.0 - accuracy)

        start_x = self.width // 2
        start_y = 5

        self.ball = Ball(x=start_x, y=start_y)

        distance = ((target_x - start_x)**2 + (target_y - start_y)**2)**0.5
        speed = 0.5 + (self.ai_shot_power * 1.5)

        if distance > 0:
            self.ball.vx = (target_x - start_x) / distance * speed
            self.ball.vy = (target_y - start_y) / distance * speed

    def check_goal(self):
        """Check if shot resulted in a goal"""
        if not self.ball:
            return

        goal_left = self.width // 2 - 25
        goal_right = self.width // 2 + 25
        goal_top = 5
        goal_bottom = 18

        # Check if in goal
        if (goal_left <= self.ball.x <= goal_right and
            goal_top <= self.ball.y <= goal_bottom):

            # Check if goalkeeper saved it
            if self.goalkeeper.is_diving and self.goalkeeper.dive_progress > 0.5:
                zone_col = self.selected_zone.value % 3
                correct_dive = False

                if zone_col == 0 and self.goalkeeper.dive_direction == "left":
                    correct_dive = True
                elif zone_col == 2 and self.goalkeeper.dive_direction == "right":
                    correct_dive = True
                elif zone_col == 1 and self.goalkeeper.dive_direction == "center":
                    correct_dive = True

                if correct_dive and random.random() < 0.7:  # 70% save chance if correct
                    self.result_message = "SAVED! Goalkeeper got it!"
                    self.result_timer = 90
                    return

            # GOAL!
            self.goals_scored += 1
            self.score_player += 1

            # Check if perfect shot
            if self.power_level > 0.8 and self.selected_zone.value in [0, 2, 6, 8]:
                self.result_message = "UNSTOPPABLE! Top corner!"
                self.perfect_shots += 1
            else:
                self.result_message = "GOAL! What a strike!"

        else:
            self.result_message = "MISSED! Off target!"

        self.result_timer = 90
        self.ball = None

    def check_save(self):
        """Check if goalkeeper saved the shot"""
        if not self.ball:
            return

        goal_left = self.width // 2 - 25
        goal_right = self.width // 2 + 25

        # Check if in goal area
        if goal_left <= self.ball.x <= goal_right:
            # Check if player saved it
            if self.goalkeeper.is_diving:
                zone_col = self.ai_shot_zone.value % 3
                correct_dive = False

                if zone_col == 0 and self.goalkeeper.dive_direction == "left":
                    correct_dive = True
                elif zone_col == 2 and self.goalkeeper.dive_direction == "right":
                    correct_dive = True
                elif zone_col == 1 and self.goalkeeper.dive_direction == "center":
                    correct_dive = True

                if correct_dive:
                    self.result_message = f"SAVED! Great {self.goalkeeper.hand_used} hand!"
                    self.saves_made += 1
                    self.result_timer = 90
                    return

            # Goal scored by AI
            self.result_message = "GOAL! They scored!"
            self.score_opponent += 1
        else:
            self.result_message = "They missed!"

        self.result_timer = 90
        self.ball = None

    def draw_menu(self):
        """Draw main menu"""
        self.stdscr.clear()

        title = [
            "╔════════════════════════════════════════════════╗",
            "║                                                ║",
            "║        PENALTY SHOOTOUT                        ║",
            "║        Terminal Edition                        ║",
            "║                                                ║",
            "╚════════════════════════════════════════════════╝",
        ]

        start_y = max(2, self.height // 2 - 12)

        for i, line in enumerate(title):
            if start_y + i < self.height - 1:
                x = max(0, (self.width - len(line)) // 2)
                color = curses.color_pair(1) | curses.A_BOLD
                try:
                    self.stdscr.addstr(start_y + i, x, line[:self.width-1], color)
                except:
                    pass

        menu_items = [
            "",
            "[1] Shooter Mode - Take penalties",
            "[2] Goalkeeper Mode - Save penalties",
            "[3] Tournament - Best of 5",
            "",
            "[Q] Quit",
            "",
            "SHOOTER CONTROLS:",
            "  Arrow Keys - Aim at goal zones",
            "  SPACE (hold) - Power bar, release to shoot",
            "  C - Chip shot",
            "",
            "GOALKEEPER CONTROLS:",
            "  A - Dive LEFT (left hand)",
            "  D - Dive RIGHT (right hand)",
            "  S - Stay CENTER (both hands)",
            "  W - Jump UP (both hands)",
        ]

        for i, line in enumerate(menu_items):
            y = start_y + len(title) + i + 1
            if y < self.height - 1:
                x = max(0, (self.width - len(line)) // 2)
                if line.startswith("["):
                    color = curses.color_pair(2) | curses.A_BOLD
                else:
                    color = curses.color_pair(6)
                try:
                    self.stdscr.addstr(y, x, line[:self.width-1], color)
                except:
                    pass

    def draw_goal(self):
        """Draw the goal"""
        goal_left = self.width // 2 - 25
        goal_right = self.width // 2 + 25
        goal_top = 5
        goal_bottom = 18

        # Goal posts
        for y in range(goal_top, goal_bottom + 1):
            try:
                self.stdscr.addstr(y, goal_left, '|', curses.color_pair(5) | curses.A_BOLD)
                self.stdscr.addstr(y, goal_right, '|', curses.color_pair(5) | curses.A_BOLD)
            except:
                pass

        # Crossbar
        for x in range(goal_left, goal_right + 1):
            try:
                self.stdscr.addstr(goal_top, x, '=', curses.color_pair(5) | curses.A_BOLD)
            except:
                pass

        # Net
        for y in range(goal_top + 1, goal_bottom):
            for x in range(goal_left + 1, goal_right):
                if (x + y) % 3 == 0:
                    try:
                        self.stdscr.addstr(y, x, '.', curses.color_pair(6) | curses.A_DIM)
                    except:
                        pass

    def draw_zone_selector(self):
        """Draw the zone selection grid"""
        if self.shot_taken:
            return

        goal_left = self.width // 2 - 25
        goal_right = self.width // 2 + 25
        goal_top = 5
        goal_bottom = 18

        zone_width = (goal_right - goal_left) // 3
        zone_height = (goal_bottom - goal_top) // 3

        for zone in Zone:
            zone_col = zone.value % 3
            zone_row = zone.value // 3

            x = goal_left + (zone_col * zone_width) + zone_width // 2
            y = goal_top + (zone_row * zone_height) + zone_height // 2

            if zone == self.selected_zone:
                char = 'X'
                color = curses.color_pair(7) | curses.A_BOLD
            else:
                char = '+'
                color = curses.color_pair(6) | curses.A_DIM

            try:
                self.stdscr.addstr(y, x, char, color)
            except:
                pass

    def draw_power_bar(self):
        """Draw the power charging bar"""
        if self.shot_taken:
            return

        bar_y = self.height - 8
        bar_x = self.width // 2 - 15
        bar_width = 30

        # Bar outline
        try:
            self.stdscr.addstr(bar_y, bar_x, '[' + ' ' * bar_width + ']', curses.color_pair(6))

            # Fill
            fill_width = int(self.power_level * bar_width)
            if fill_width > 0:
                fill_color = curses.color_pair(7) if self.power_level < 0.8 else curses.color_pair(4)
                self.stdscr.addstr(bar_y, bar_x + 1, '=' * fill_width, fill_color | curses.A_BOLD)

            # Label
            label = f"POWER: {int(self.power_level * 100)}%"
            if self.is_charging_power:
                label += " (CHARGING)"
            self.stdscr.addstr(bar_y - 1, bar_x, label, curses.color_pair(6))
        except:
            pass

    def draw_goalkeeper(self):
        """Draw the goalkeeper"""
        gk = self.goalkeeper

        if gk.is_diving and gk.dive_progress > 0:
            # Diving animation
            if gk.dive_direction == "left":
                offset_x = int(-10 * gk.dive_progress)
                char = '<'
                hand_char = '('
            elif gk.dive_direction == "right":
                offset_x = int(10 * gk.dive_progress)
                char = '>'
                hand_char = ')'
            else:
                offset_x = 0
                char = '|'
                hand_char = '='

            x = int(gk.x + offset_x)
            y = int(gk.y)

            try:
                # Draw hands
                if gk.hand_used in ["left", "both"]:
                    self.stdscr.addstr(y - 1, x - 1, hand_char, curses.color_pair(4) | curses.A_BOLD)
                if gk.hand_used in ["right", "both"]:
                    self.stdscr.addstr(y - 1, x + 1, hand_char, curses.color_pair(4) | curses.A_BOLD)

                # Draw body
                self.stdscr.addstr(y, x, char, curses.color_pair(4) | curses.A_BOLD)
            except:
                pass
        else:
            # Standing
            try:
                self.stdscr.addstr(int(gk.y), int(gk.x), 'H', curses.color_pair(4) | curses.A_BOLD)
            except:
                pass

    def draw_ball(self):
        """Draw the ball"""
        if self.ball:
            try:
                char = 'O' if not self.ball.spinning else '@'
                self.stdscr.addstr(int(self.ball.y), int(self.ball.x), char,
                                 curses.color_pair(2) | curses.A_BOLD)
            except:
                pass

    def draw_shooter_mode(self):
        """Draw shooter mode screen"""
        self.stdscr.clear()

        # Draw field
        for x in range(0, self.width):
            try:
                self.stdscr.addstr(self.height - 3, x, '=', curses.color_pair(1))
            except:
                pass

        self.draw_goal()
        self.draw_zone_selector()
        self.draw_goalkeeper()
        self.draw_ball()
        self.draw_power_bar()

        # Instructions
        try:
            self.stdscr.addstr(2, 2, "SHOOTER MODE", curses.color_pair(3) | curses.A_BOLD)
            self.stdscr.addstr(3, 2, f"Goals: {self.goals_scored}/{self.shots_taken}", curses.color_pair(1))
        except:
            pass

        # Result message
        if self.result_message and self.result_timer > 0:
            try:
                msg_x = self.width // 2 - len(self.result_message) // 2
                self.stdscr.addstr(self.height // 2, msg_x, self.result_message,
                                 curses.color_pair(1) | curses.A_BOLD if "GOAL" in self.result_message
                                 else curses.color_pair(4) | curses.A_BOLD)
                self.stdscr.addstr(self.height // 2 + 2, self.width // 2 - 15,
                                 "[SPACE] Next  [Q] Menu", curses.color_pair(6))
            except:
                pass

    def draw_goalkeeper_mode(self):
        """Draw goalkeeper mode screen"""
        self.stdscr.clear()

        # Draw field
        for x in range(0, self.width):
            try:
                self.stdscr.addstr(self.height - 3, x, '=', curses.color_pair(1))
            except:
                pass

        self.draw_goal()
        self.draw_ball()

        # Draw player as goalkeeper
        gk_y = self.height - 15
        self.goalkeeper.y = gk_y
        self.draw_goalkeeper()

        # Instructions
        try:
            self.stdscr.addstr(2, 2, "GOALKEEPER MODE", curses.color_pair(4) | curses.A_BOLD)
            self.stdscr.addstr(3, 2, f"Saves: {self.saves_made}", curses.color_pair(1))

            if self.ai_shot_delay > 0:
                countdown = (self.ai_shot_delay // 30) + 1
                self.stdscr.addstr(self.height // 2, self.width // 2 - 10,
                                 f"Get ready... {countdown}", curses.color_pair(7) | curses.A_BOLD)
        except:
            pass

        # Result message
        if self.result_message and self.result_timer > 0:
            try:
                msg_x = self.width // 2 - len(self.result_message) // 2
                color = curses.color_pair(1) if "SAVED" in self.result_message else curses.color_pair(4)
                self.stdscr.addstr(self.height // 2, msg_x, self.result_message, color | curses.A_BOLD)
                self.stdscr.addstr(self.height // 2 + 2, self.width // 2 - 15,
                                 "[SPACE] Next  [Q] Menu", curses.color_pair(6))
            except:
                pass

    def run(self):
        """Main game loop"""
        while True:
            try:
                key = self.stdscr.getch()
            except:
                key = -1

            if key != -1:
                if not self.handle_input(key):
                    break

            # Update physics
            self.update_physics()

            # Draw
            try:
                if self.mode == GameMode.MENU:
                    self.draw_menu()
                elif self.mode == GameMode.SHOOTER:
                    self.draw_shooter_mode()
                elif self.mode == GameMode.GOALKEEPER:
                    self.draw_goalkeeper_mode()

                self.stdscr.refresh()
            except:
                pass

            time.sleep(0.03)


def main(stdscr):
    """Main entry point"""
    try:
        game = PenaltyShootout(stdscr)
        game.run()
    except Exception as e:
        curses.endwin()
        print(f"\n❌ Error: {e}")
        raise


def main_wrapper():
    """Wrapper for console script"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ['--version', '-v']:
        print("Penalty Shootout v1.0.0")
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("⚽ Penalty Shootout - Terminal Edition")
        print("\nUsage: penalty")
        print("\nModes:")
        print("  [1] Shooter Mode - Take penalties")
        print("  [2] Goalkeeper Mode - Save penalties")
        print("  [3] Tournament - Best of 5")
        sys.exit(0)

    if 'TERM' not in os.environ or os.environ['TERM'] == 'unknown':
        os.environ['TERM'] = 'xterm-256color'

    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\n\n⚽ Game Over! Thanks for playing!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main_wrapper()
