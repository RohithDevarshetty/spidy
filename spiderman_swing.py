#!/usr/bin/env python3
"""
Spiderman Swinging Game - A Terminal-Based Adventure
Swing through the city, avoid obstacles, and rack up points!
"""

import curses
import random
import math
import time
import os
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

# Game Constants
GRAVITY = 0.4
SWING_STRENGTH = 1.8
MAX_ROPE_LENGTH = 25
MIN_BUILDING_HEIGHT = 8
MAX_BUILDING_HEIGHT = 35
BUILDING_WIDTH = 10
GAME_SPEED = 0.04
PARTICLE_LIFETIME = 15
MAX_PARTICLES = 50


class GameState(Enum):
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2
    PAUSED = 3


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    char: str
    color: int
    lifetime: int


@dataclass
class Building:
    x: int
    height: int
    width: int = BUILDING_WIDTH
    has_obstacle: bool = False
    obstacle_height: int = 0
    color_variant: int = 0


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
    animation_frame: int = 0


class SpidermanGame:
    def __init__(self, stdscr):
        self.stdscr = stdscr

        # Check terminal support
        if not self._check_terminal():
            raise RuntimeError("Terminal does not support required features")

        self.height, self.width = stdscr.getmaxyx()
        self.state = GameState.MENU
        self.score = 0
        self.high_score = 0
        self.combo = 0
        self.max_combo = 0

        # Initialize curses
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(1)   # Non-blocking input
        stdscr.timeout(30)  # 30ms timeout for smoother gameplay

        # Try to use default colors for better terminal compatibility
        try:
            curses.use_default_colors()
        except:
            pass

        # Initialize colors with more variety
        self._init_colors()

        self.spiderman = None
        self.buildings: List[Building] = []
        self.particles: List[Particle] = []
        self.camera_x = 0
        self.frame_count = 0

    def _check_terminal(self) -> bool:
        """Check if terminal supports required features"""
        try:
            # Set a default TERM if not set
            if 'TERM' not in os.environ or os.environ['TERM'] == 'unknown':
                os.environ['TERM'] = 'xterm-256color'
            return True
        except:
            return False

    def _init_colors(self):
        """Initialize color pairs with enhanced palette"""
        curses.start_color()

        # Try to enable extended colors if available
        try:
            if curses.can_change_color() and curses.COLORS >= 256:
                # Enhanced mode with custom colors
                curses.init_pair(1, 196, -1)    # Bright Red - Spiderman
                curses.init_pair(2, 21, -1)     # Deep Blue - Buildings
                curses.init_pair(3, 39, -1)     # Cyan - Building fill
                curses.init_pair(4, 226, -1)    # Bright Yellow - Web
                curses.init_pair(5, 46, -1)     # Bright Green - Score
                curses.init_pair(6, 201, -1)    # Magenta - Obstacles
                curses.init_pair(7, 202, -1)    # Orange - Effects
                curses.init_pair(8, 27, -1)     # Blue - Sky elements
                curses.init_pair(9, 240, -1)    # Gray - Building accents
                curses.init_pair(10, 51, -1)    # Cyan - Web glow
                curses.init_pair(11, 160, -1)   # Dark Red - Spidey trail
                curses.init_pair(12, 220, -1)   # Gold - Combo text
                curses.init_pair(13, 93, -1)    # Purple - Special effects
                curses.init_pair(14, 118, -1)   # Light Green - Buildings variant
                curses.init_pair(15, 208, -1)   # Orange - Windows
            else:
                raise Exception("Fallback to 8 colors")
        except:
            # Fallback to basic 8 colors
            curses.init_pair(1, curses.COLOR_RED, -1)
            curses.init_pair(2, curses.COLOR_BLUE, -1)
            curses.init_pair(3, curses.COLOR_CYAN, -1)
            curses.init_pair(4, curses.COLOR_YELLOW, -1)
            curses.init_pair(5, curses.COLOR_GREEN, -1)
            curses.init_pair(6, curses.COLOR_MAGENTA, -1)
            curses.init_pair(7, curses.COLOR_RED, -1)
            curses.init_pair(8, curses.COLOR_BLUE, -1)
            curses.init_pair(9, curses.COLOR_WHITE, -1)
            curses.init_pair(10, curses.COLOR_CYAN, -1)
            curses.init_pair(11, curses.COLOR_RED, -1)
            curses.init_pair(12, curses.COLOR_YELLOW, -1)
            curses.init_pair(13, curses.COLOR_MAGENTA, -1)
            curses.init_pair(14, curses.COLOR_GREEN, -1)
            curses.init_pair(15, curses.COLOR_YELLOW, -1)

    def init_game(self):
        """Initialize a new game"""
        self.state = GameState.PLAYING
        self.score = 0
        self.combo = 0
        start_x = 20
        start_y = self.height - 15

        self.spiderman = SpiderMan(x=start_x, y=start_y)
        self.buildings = []
        self.particles = []
        self.camera_x = 0
        self.frame_count = 0

        # Generate initial buildings
        for i in range(15):
            self.buildings.append(self.generate_building(i * 15))

    def generate_building(self, base_x: int) -> Building:
        """Generate a random building"""
        height = random.randint(MIN_BUILDING_HEIGHT, MAX_BUILDING_HEIGHT)
        has_obstacle = random.random() < 0.25  # 25% chance
        obstacle_height = random.randint(int(height * 0.3), int(height * 0.7)) if has_obstacle and height > 12 else 0
        color_variant = random.randint(0, 2)

        return Building(
            x=base_x,
            height=height,
            has_obstacle=has_obstacle,
            obstacle_height=obstacle_height,
            color_variant=color_variant
        )

    def add_particle(self, x: float, y: float, vx: float, vy: float, char: str, color: int):
        """Add a particle effect"""
        if len(self.particles) < MAX_PARTICLES:
            self.particles.append(Particle(x, y, vx, vy, char, color, PARTICLE_LIFETIME))

    def create_web_particles(self):
        """Create particles when shooting web"""
        spidy = self.spiderman
        for _ in range(5):
            angle = random.uniform(-0.5, 0.5)
            speed = random.uniform(1, 3)
            self.add_particle(
                spidy.x, spidy.y,
                speed * math.cos(angle), speed * math.sin(angle),
                random.choice(['*', '+', '·', '•']),
                10  # Cyan glow
            )

    def create_swing_trail(self):
        """Create trail particles while swinging"""
        if random.random() < 0.4:
            spidy = self.spiderman
            self.add_particle(
                spidy.x, spidy.y,
                spidy.vx * 0.3, spidy.vy * 0.3,
                random.choice(['~', '≈', '∼']),
                11  # Red trail
            )

    def create_obstacle_hit_effect(self, x: float, y: float):
        """Create explosion effect when hitting obstacle"""
        for i in range(12):
            angle = (i / 12) * 2 * math.pi
            speed = random.uniform(2, 4)
            self.add_particle(
                x, y,
                speed * math.cos(angle), speed * math.sin(angle),
                random.choice(['*', '#', '@', '!']),
                7  # Orange
            )

    def update_particles(self):
        """Update all particle positions and lifetimes"""
        for particle in self.particles:
            particle.x += particle.vx
            particle.y += particle.vy
            particle.vy += 0.2  # Gravity
            particle.vx *= 0.95  # Air resistance
            particle.lifetime -= 1

        # Remove dead particles
        self.particles = [p for p in self.particles if p.lifetime > 0]

    def update_buildings(self):
        """Update buildings and generate new ones"""
        # Remove buildings off-screen
        self.buildings = [b for b in self.buildings if b.x + b.width > self.camera_x - 20]

        # Add new buildings
        if self.buildings:
            last_building = max(self.buildings, key=lambda b: b.x)
            while last_building.x < self.camera_x + self.width + 50:
                gap = random.randint(12, 25)
                new_x = last_building.x + last_building.width + gap
                self.buildings.append(self.generate_building(new_x))
                last_building = self.buildings[-1]

    def handle_input(self, key):
        """Handle keyboard input"""
        if self.state == GameState.MENU:
            if key in [ord('s'), ord('S'), ord(' ')]:
                self.init_game()
            elif key == ord('q'):
                return False

        elif self.state == GameState.PLAYING:
            if key == ord(' '):
                if not self.spiderman.is_swinging:
                    self.shoot_web()
                else:
                    # Release web early
                    self.spiderman.is_swinging = False
            elif key == ord('q'):
                self.state = GameState.MENU
            elif key == ord('p'):
                self.state = GameState.PAUSED

        elif self.state == GameState.PAUSED:
            if key == ord('p'):
                self.state = GameState.PLAYING
            elif key == ord('q'):
                self.state = GameState.MENU

        elif self.state == GameState.GAME_OVER:
            if key in [ord('r'), ord('R'), ord(' ')]:
                self.init_game()
            elif key == ord('q'):
                self.state = GameState.MENU

        return True

    def shoot_web(self):
        """Shoot web to the nearest building anchor point"""
        if not self.spiderman.is_swinging:
            nearest = None
            min_distance = float('inf')

            for building in self.buildings:
                # Multiple anchor points per building
                for offset in [0.3, 0.5, 0.7]:
                    bldg_top_x = building.x + building.width * offset
                    bldg_top_y = self.height - building.height - 1

                    # Only consider points ahead and above
                    if bldg_top_x > self.spiderman.x - 5:
                        dx = bldg_top_x - self.spiderman.x
                        dy = bldg_top_y - self.spiderman.y
                        distance = math.sqrt(dx * dx + dy * dy)

                        if distance < MAX_ROPE_LENGTH and distance < min_distance:
                            min_distance = distance
                            nearest = (bldg_top_x, bldg_top_y)

            if nearest:
                self.spiderman.is_swinging = True
                self.spiderman.swing_anchor_x = nearest[0]
                self.spiderman.swing_anchor_y = nearest[1]
                self.spiderman.rope_length = min_distance
                self.create_web_particles()
                self.combo += 1
                self.max_combo = max(self.max_combo, self.combo)

    def update_physics(self):
        """Update game physics"""
        if self.state != GameState.PLAYING:
            return

        spidy = self.spiderman
        self.frame_count += 1
        spidy.animation_frame = (spidy.animation_frame + 1) % 20

        if spidy.is_swinging:
            # Swinging physics with pendulum motion
            dx = spidy.x - spidy.swing_anchor_x
            dy = spidy.y - spidy.swing_anchor_y
            current_distance = math.sqrt(dx**2 + dy**2)

            if current_distance > 0.1:
                angle = math.atan2(dy, dx)

                # Constrain to rope length
                if current_distance > spidy.rope_length:
                    spidy.x = spidy.swing_anchor_x + spidy.rope_length * math.cos(angle)
                    spidy.y = spidy.swing_anchor_y + spidy.rope_length * math.sin(angle)

                    # Tangential velocity
                    tangent_x = -math.sin(angle)
                    tangent_y = math.cos(angle)

                    v_tangent = spidy.vx * tangent_x + spidy.vy * tangent_y

                    # Apply gravity along tangent
                    gravity_component = GRAVITY * math.cos(angle)
                    v_tangent += gravity_component * 0.5

                    # Update velocity
                    spidy.vx = v_tangent * tangent_x * 1.02
                    spidy.vy = v_tangent * tangent_y * 1.02

                # Auto-release at optimal point
                if spidy.vy < -3 and dy < 0:
                    spidy.is_swinging = False
                    spidy.vy *= 1.1  # Boost on release

            self.create_swing_trail()
        else:
            # Free fall
            spidy.vy += GRAVITY
            spidy.vx *= 0.985  # Air resistance
            self.combo = 0

        # Apply velocity
        spidy.x += spidy.vx
        spidy.y += spidy.vy

        # Smooth camera follow
        target_camera_x = spidy.x - self.width // 4
        self.camera_x += (target_camera_x - self.camera_x) * 0.15

        # Update particles
        self.update_particles()

        # Check collisions
        self.check_collisions()

        # Update score
        self.score = max(self.score, int(spidy.x // 5))

        # Update buildings
        self.update_buildings()

    def check_collisions(self):
        """Check for collisions"""
        spidy = self.spiderman
        ground_level = self.height - 2

        # Ground collision
        if spidy.y >= ground_level:
            self.game_over()
            return

        # Building collisions
        for building in self.buildings:
            bldg_top = self.height - building.height
            bldg_left = building.x
            bldg_right = building.x + building.width

            if (bldg_left - 1 <= spidy.x <= bldg_right + 1 and
                spidy.y >= bldg_top - 1):

                # Hit obstacle
                if building.has_obstacle:
                    obstacle_y = self.height - building.obstacle_height
                    if abs(spidy.y - obstacle_y) < 2:
                        self.create_obstacle_hit_effect(spidy.x, spidy.y)
                        self.game_over()
                        return

    def game_over(self):
        """Handle game over"""
        self.state = GameState.GAME_OVER
        self.high_score = max(self.high_score, self.score)

    def draw_menu(self):
        """Draw the main menu with style"""
        self.stdscr.clear()

        title = [
            "  ███████╗██████╗ ██╗██████╗ ███████╗██████╗ ███╗   ███╗ █████╗ ███╗   ██╗",
            "  ██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔══██╗████╗ ████║██╔══██╗████╗  ██║",
            "  ███████╗██████╔╝██║██║  ██║█████╗  ██████╔╝██╔████╔██║███████║██╔██╗ ██║",
            "  ╚════██║██╔═══╝ ██║██║  ██║██╔══╝  ██╔══██╗██║╚██╔╝██║██╔══██║██║╚██╗██║",
            "  ███████║██║     ██║██████╔╝███████╗██║  ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║",
            "  ╚══════╝╚═╝     ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝",
            "",
            "                    🕷️  S W I N G  T H R O U G H  T H E  C I T Y  🕷️",
        ]

        start_y = max(2, self.height // 2 - len(title) - 8)

        # Animated title
        for i, line in enumerate(title):
            if start_y + i < self.height - 1:
                x = max(0, (self.width - len(line)) // 2)
                color = curses.color_pair(1) if i < 6 else curses.color_pair(12)
                try:
                    self.stdscr.addstr(start_y + i, min(x, self.width - 2),
                                     line[:self.width-1], color | curses.A_BOLD)
                except:
                    pass

        instructions = [
            "",
            "╔══════════════════════════════════════════════════════════╗",
            "║                      CONTROLS                            ║",
            "║  [SPACE] - Shoot Web / Release Web                      ║",
            "║  [P]     - Pause Game                                    ║",
            "║  [Q]     - Quit                                          ║",
            "╚══════════════════════════════════════════════════════════╝",
            "",
            "🎯 Objective: Swing through the city without hitting the ground!",
            "              Build combos by chaining swings!",
            "",
            "✨ Press [SPACE] to start your adventure! ✨",
        ]

        for i, line in enumerate(instructions):
            y = start_y + len(title) + i + 1
            if y < self.height - 1:
                x = max(0, (self.width - len(line)) // 2)
                if "SPACE" in line or "start" in line:
                    color = curses.color_pair(5) | curses.A_BOLD | curses.A_BLINK
                elif "══" in line or "║" in line:
                    color = curses.color_pair(4)
                else:
                    color = curses.color_pair(9)
                try:
                    self.stdscr.addstr(y, min(x, self.width - 2),
                                     line[:self.width-1], color)
                except:
                    pass

        if self.high_score > 0:
            score_text = f"🏆 HIGH SCORE: {self.high_score} 🏆  Max Combo: x{self.max_combo}"
            try:
                y = self.height - 3
                x = max(0, (self.width - len(score_text)) // 2)
                self.stdscr.addstr(y, min(x, self.width - 2),
                                 score_text[:self.width-1],
                                 curses.color_pair(12) | curses.A_BOLD)
            except:
                pass

    def draw_game_over(self):
        """Draw game over screen"""
        self.stdscr.clear()

        # Draw faded game state
        self.draw_game_background()

        # Game over overlay
        game_over_text = [
            "╔═══════════════════════════════════════════════════════════╗",
            "║   ██████╗  █████╗ ███╗   ███╗███████╗                    ║",
            "║  ██╔════╝ ██╔══██╗████╗ ████║██╔════╝                    ║",
            "║  ██║  ███╗███████║██╔████╔██║█████╗                      ║",
            "║  ██║   ██║██╔══██║██║╚██╔╝██║██╔══╝                      ║",
            "║  ╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗                    ║",
            "║   ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝                    ║",
            "║                                                           ║",
            "║   ██████╗ ██╗   ██╗███████╗██████╗                       ║",
            "║  ██╔═══██╗██║   ██║██╔════╝██╔══██╗                      ║",
            "║  ██║   ██║██║   ██║█████╗  ██████╔╝                      ║",
            "║  ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗                      ║",
            "║  ╚██████╔╝ ╚████╔╝ ███████╗██║  ██║                      ║",
            "║   ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝                      ║",
            "╚═══════════════════════════════════════════════════════════╝",
        ]

        start_y = max(2, self.height // 2 - len(game_over_text) // 2 - 3)

        for i, line in enumerate(game_over_text):
            y = start_y + i
            if 0 <= y < self.height - 1:
                x = max(0, (self.width - len(line)) // 2)
                try:
                    self.stdscr.addstr(y, min(x, self.width - 2),
                                     line[:self.width-1],
                                     curses.color_pair(1) | curses.A_BOLD)
                except:
                    pass

        # Stats
        stats = [
            f"{'═' * 50}",
            f"Final Score: {self.score}",
            f"High Score: {self.high_score}",
            f"Max Combo: x{self.max_combo}",
            f"{'═' * 50}",
            "",
            "[SPACE] Try Again    [Q] Main Menu",
        ]

        for i, line in enumerate(stats):
            y = start_y + len(game_over_text) + i + 1
            if 0 <= y < self.height - 1:
                x = max(0, (self.width - len(line)) // 2)
                color = curses.color_pair(12) if "Score" in line or "Combo" in line else curses.color_pair(5)
                try:
                    self.stdscr.addstr(y, min(x, self.width - 2),
                                     line[:self.width-1], color | curses.A_BOLD)
                except:
                    pass

    def draw_game_background(self):
        """Draw game background"""
        # Simple sky gradient
        for y in range(0, self.height - 2):
            if y % 4 == 0:
                char = '·' if random.random() < 0.1 else ' '
                color = curses.color_pair(8)
                for x in range(0, self.width, 3):
                    try:
                        self.stdscr.addstr(y, x, char, color)
                    except:
                        pass

    def draw_game(self):
        """Draw the game state with enhanced graphics"""
        self.stdscr.clear()

        # Draw sky
        self.draw_game_background()

        # Draw particles first (background layer)
        for particle in self.particles:
            screen_x = int(particle.x - self.camera_x)
            screen_y = int(particle.y)
            if 0 <= screen_x < self.width - 1 and 0 <= screen_y < self.height - 1:
                alpha = particle.lifetime / PARTICLE_LIFETIME
                if alpha > 0.3:
                    try:
                        attr = curses.color_pair(particle.color)
                        if alpha > 0.7:
                            attr |= curses.A_BOLD
                        self.stdscr.addstr(screen_y, screen_x, particle.char, attr)
                    except:
                        pass

        # Draw buildings with enhanced graphics
        for building in self.buildings:
            screen_x = int(building.x - self.camera_x)

            if -building.width <= screen_x <= self.width:
                bldg_top = self.height - building.height

                # Select color based on variant
                if building.color_variant == 0:
                    fill_color = curses.color_pair(3)
                    edge_color = curses.color_pair(2)
                elif building.color_variant == 1:
                    fill_color = curses.color_pair(14)
                    edge_color = curses.color_pair(2)
                else:
                    fill_color = curses.color_pair(9)
                    edge_color = curses.color_pair(8)

                # Draw building
                for y in range(bldg_top, self.height - 1):
                    for x in range(building.width):
                        draw_x = screen_x + x
                        if 0 <= draw_x < self.width - 1 and 0 <= y < self.height - 1:
                            # Building pattern
                            is_edge = (x == 0 or x == building.width - 1 or y == bldg_top)
                            is_window = (x % 3 == 1 and y % 4 == 2)

                            if is_edge:
                                char = '█'
                                color = edge_color | curses.A_BOLD
                            elif is_window:
                                char = '▓' if random.random() < 0.7 else '▒'
                                color = curses.color_pair(15)
                            else:
                                char = '░'
                                color = fill_color

                            try:
                                self.stdscr.addstr(y, draw_x, char, color)
                            except:
                                pass

                # Draw obstacle with style
                if building.has_obstacle:
                    obstacle_y = self.height - building.obstacle_height
                    for x in range(1, building.width - 1):
                        draw_x = screen_x + x
                        if 0 <= draw_x < self.width - 1 and 0 <= obstacle_y < self.height - 1:
                            char = '▼' if x % 2 == 0 else '▽'
                            try:
                                self.stdscr.addstr(obstacle_y, draw_x, char,
                                                 curses.color_pair(6) | curses.A_BOLD | curses.A_BLINK)
                            except:
                                pass

        # Draw web rope with style
        if self.spiderman.is_swinging:
            rope_x = int(self.spiderman.swing_anchor_x - self.camera_x)
            rope_y = int(self.spiderman.swing_anchor_y)
            spidy_x = int(self.spiderman.x - self.camera_x)
            spidy_y = int(self.spiderman.y)

            # Draw web line
            steps = max(abs(rope_x - spidy_x), abs(rope_y - spidy_y))
            if steps > 0:
                for i in range(steps):
                    t = i / steps
                    x = int(rope_x + (spidy_x - rope_x) * t)
                    y = int(rope_y + (spidy_y - rope_y) * t)

                    if 0 <= x < self.width - 1 and 0 <= y < self.height - 1:
                        # Varied web pattern
                        if i % 3 == 0:
                            char = '╱' if (spidy_x - rope_x) > 0 else '╲'
                        elif i % 3 == 1:
                            char = '│'
                        else:
                            char = '/'

                        color = curses.color_pair(4) if i % 2 == 0 else curses.color_pair(10)
                        try:
                            self.stdscr.addstr(y, x, char, color | curses.A_BOLD)
                        except:
                            pass

            # Draw anchor point
            if 0 <= rope_x < self.width - 1 and 0 <= rope_y < self.height - 1:
                try:
                    self.stdscr.addstr(rope_y, rope_x, '⚓',
                                     curses.color_pair(4) | curses.A_BOLD)
                except:
                    pass

        # Draw Spiderman with animation
        spidy_screen_x = int(self.spiderman.x - self.camera_x)
        spidy_screen_y = int(self.spiderman.y)

        if 0 <= spidy_screen_x < self.width - 1 and 0 <= spidy_screen_y < self.height - 1:
            # Animated character
            if self.spiderman.is_swinging:
                chars = ['🕷', '⚡', '💫', '✨']
                spidy_char = chars[self.spiderman.animation_frame % len(chars)]
            else:
                spidy_char = '●'

            try:
                self.stdscr.addstr(spidy_screen_y, spidy_screen_x, spidy_char,
                                 curses.color_pair(1) | curses.A_BOLD)
            except:
                pass

        # Draw HUD
        self.draw_hud()

    def draw_hud(self):
        """Draw heads-up display"""
        try:
            # Top left - Score and stats
            score_text = f"🏆 Score: {self.score}"
            speed = math.sqrt(self.spiderman.vx**2 + self.spiderman.vy**2)
            speed_text = f"⚡ Speed: {speed:.1f}"

            self.stdscr.addstr(0, 2, score_text, curses.color_pair(12) | curses.A_BOLD)
            self.stdscr.addstr(1, 2, speed_text, curses.color_pair(5))

            # Combo counter
            if self.combo > 1:
                combo_text = f"🔥 COMBO x{self.combo}!"
                color = curses.color_pair(7) | curses.A_BOLD
                if self.combo > 5:
                    color |= curses.A_BLINK
                self.stdscr.addstr(2, 2, combo_text, color)

            # Status
            status = "SWINGING!" if self.spiderman.is_swinging else "Free Fall"
            status_color = curses.color_pair(4) if self.spiderman.is_swinging else curses.color_pair(6)
            self.stdscr.addstr(0, self.width - 25, f"Status: {status}", status_color | curses.A_BOLD)

            # Controls reminder
            controls = "[SPACE] Web  [P] Pause  [Q] Quit"
            self.stdscr.addstr(self.height - 1, 2, controls, curses.color_pair(9))

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

            # Update game state
            if self.state == GameState.PLAYING:
                self.update_physics()

            # Draw
            try:
                if self.state == GameState.MENU:
                    self.draw_menu()
                elif self.state == GameState.PLAYING:
                    self.draw_game()
                elif self.state == GameState.GAME_OVER:
                    self.draw_game_over()
                elif self.state == GameState.PAUSED:
                    self.draw_game()
                    # Draw pause overlay
                    pause_text = "⏸ PAUSED - Press [P] to continue ⏸"
                    y = self.height // 2
                    x = max(0, (self.width - len(pause_text)) // 2)
                    self.stdscr.addstr(y, x, pause_text,
                                     curses.color_pair(12) | curses.A_BOLD | curses.A_BLINK)

                self.stdscr.refresh()
            except:
                pass

            time.sleep(GAME_SPEED)


def main(stdscr):
    """Main entry point"""
    try:
        game = SpidermanGame(stdscr)
        game.run()
    except Exception as e:
        # Cleanup curses before showing error
        curses.endwin()
        print(f"\n❌ Error running game: {e}")
        print("\n💡 Make sure you're running this in a proper terminal window.")
        print("   For best results, use a terminal with 256-color support.\n")
        raise


def main_wrapper():
    """Wrapper for console script entry point"""
    import sys

    # Handle version flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--version', '-v']:
        print("Spidy - Spiderman Swinging Game v1.0.0")
        print("A terminal-based adventure game with crazy graphics!")
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("🕷️  Spidy - Spiderman Swinging Game")
        print("\nUsage: spidy")
        print("\nControls:")
        print("  SPACE - Shoot web and swing")
        print("  P     - Pause game")
        print("  Q     - Quit game")
        print("\nObjective: Swing through the city without hitting the ground!")
        print("           Chain swings together to build combos!")
        print("\n💡 For the best experience:")
        print("   - Maximize your terminal window (at least 120x40)")
        print("   - Use a terminal with 256-color support")
        print("   - Try iTerm2, Terminal.app, or modern terminal emulators\n")
        sys.exit(0)

    # Set terminal for better compatibility
    if 'TERM' not in os.environ or os.environ['TERM'] == 'unknown':
        os.environ['TERM'] = 'xterm-256color'

    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\n\n👋 Thanks for playing Spidy! See you next time!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Try running in a different terminal or check your terminal settings.\n")
        sys.exit(1)


if __name__ == "__main__":
    main_wrapper()
