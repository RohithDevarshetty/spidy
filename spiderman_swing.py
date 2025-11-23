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
GRAVITY = 0.25  # Further reduced for much easier control
SWING_STRENGTH = 1.8
MAX_ROPE_LENGTH = 30  # Increased for easier web shooting at start
MIN_BUILDING_HEIGHT = 8
MAX_BUILDING_HEIGHT = 35
BUILDING_WIDTH = 10
GAME_SPEED = 0.03  # Base game speed (normal)
SWING_SLOWMO_SPEED = 0.04  # Slower when swinging for better control (was 0.06, now faster)
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
    building_style: int = 0  # 0=modern, 1=classic, 2=art deco
    has_antenna: bool = False
    has_roof_detail: bool = False


@dataclass
class FloatingAnchor:
    """Flying anchor points for swinging in the air"""
    x: float
    y: float
    char: str = '☁'  # Cloud platform
    color: int = 8


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
    boosts_remaining: int = 10  # 10 boosts per game!


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
        self.boost_particles = []  # Track boost effect particles
        self.boost_cooldown = 0  # Prevent spam

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
        self.floating_anchors: List[FloatingAnchor] = []
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
        """Initialize a new game with auto-swing intro"""
        self.state = GameState.PLAYING
        self.score = 0
        self.combo = 0
        self.boost_cooldown = 0
        start_x = 50  # Start further right to give more room
        start_y = self.height // 3  # Start higher up

        self.spiderman = SpiderMan(x=start_x, y=start_y, vx=3.0, vy=-2.0, boosts_remaining=10)  # Start with 10 boosts!
        self.buildings = []
        self.floating_anchors = []
        self.particles = []
        self.camera_x = 0
        self.frame_count = 0

        # Create tutorial/starting platform - HUGE safe area with TALL building
        tutorial_building = Building(
            x=0,
            height=int(self.height * 0.6),  # MUCH taller - 60% of screen!
            width=60,   # Extra wide starting platform
            has_obstacle=False,
            obstacle_height=0,
            color_variant=1
        )
        self.buildings.append(tutorial_building)

        # AUTO-SWING START: Attach to starting building window
        self.spiderman.is_swinging = True
        self.spiderman.swing_anchor_x = 30  # Middle of starting building
        self.spiderman.swing_anchor_y = self.height - tutorial_building.height - 1
        self.spiderman.rope_length = math.sqrt(
            (self.spiderman.x - self.spiderman.swing_anchor_x)**2 +
            (self.spiderman.y - self.spiderman.swing_anchor_y)**2
        )

        # Generate initial buildings with progressive spacing - 50 BUILDINGS!
        x_pos = 70  # Start after the tutorial platform
        for i in range(50):  # 50 buildings!
            self.buildings.append(self.generate_building(x_pos))
            gap = self.get_building_gap(x_pos)
            x_pos += BUILDING_WIDTH + gap

        # Generate floating anchor points for aerial swinging!
        self.generate_floating_anchors()

    def generate_floating_anchors(self):
        """Generate floating anchor points scattered through the level"""
        for i in range(30):  # 30 floating platforms
            x = random.randint(100, 1500)
            y = random.randint(int(self.height * 0.2), int(self.height * 0.5))
            self.floating_anchors.append(FloatingAnchor(x=x, y=y))

    def update_floating_anchors(self):
        """Update floating anchors and generate new ones"""
        # Remove anchors off-screen
        self.floating_anchors = [a for a in self.floating_anchors if a.x > self.camera_x - 20]

        # Add new floating anchors ahead
        if self.spiderman:
            while len(self.floating_anchors) < 30:
                x = random.randint(int(self.spiderman.x + 100), int(self.spiderman.x + 300))
                y = random.randint(int(self.height * 0.2), int(self.height * 0.5))
                self.floating_anchors.append(FloatingAnchor(x=x, y=y))

    def get_difficulty_level(self, distance: float) -> float:
        """Calculate difficulty level based on distance traveled (0.0 to 1.0)"""
        # Gradually increase difficulty over distance
        # Difficulty increases from 0 to 1 over ~1500 units (longer progression)
        # First 100 units are super easy (tutorial zone)
        if distance < 100:
            return 0.0  # Tutorial zone - no difficulty
        return min(1.0, (distance - 100) / 1500.0)

    def get_building_gap(self, distance: float) -> int:
        """Calculate gap between buildings based on distance"""
        difficulty = self.get_difficulty_level(distance)
        # Start with very close buildings (8-12), gradually increase to (12-25)
        if difficulty < 0.2:
            # Early game - keep it tight and easy
            return random.randint(8, 12)
        else:
            # Progressive difficulty
            min_gap = 10
            max_gap = int(10 + difficulty * 15)  # 10-25
            return random.randint(min_gap, max_gap)

    def generate_building(self, base_x: int) -> Building:
        """Generate a random building with difficulty scaling"""
        difficulty = self.get_difficulty_level(base_x)

        # Building height progression - START WITH BIGGER BUILDINGS
        # Tutorial zone (0-20%): Medium buildings (15-25)
        # Easy (20-40%): Medium-Tall buildings (20-28)
        # Medium (40-70%): Tall buildings (22-30)
        # Hard (70-100%): Very tall buildings (25-35)
        if difficulty < 0.2:
            min_height = 15  # Much taller than before!
            max_height = 25
        elif difficulty < 0.4:
            min_height = 20
            max_height = 28
        elif difficulty < 0.7:
            min_height = 22
            max_height = 30
        else:
            min_height = 25
            max_height = 35

        height = random.randint(min_height, max_height)

        # Obstacle probability progression
        # Tutorial: 0%, Easy: 5%, Medium: 15%, Hard: 30%
        if difficulty < 0.3:
            obstacle_chance = 0.0  # No obstacles in early game
        elif difficulty < 0.5:
            obstacle_chance = 0.05  # Rare obstacles
        elif difficulty < 0.7:
            obstacle_chance = 0.15  # Some obstacles
        else:
            obstacle_chance = 0.30  # More obstacles at high difficulty

        has_obstacle = random.random() < obstacle_chance and height > 12

        # Obstacle placement
        if has_obstacle:
            # Place obstacles more strategically at higher difficulties
            obstacle_height = random.randint(
                int(height * (0.3 + difficulty * 0.2)),  # Lower bound moves up
                int(height * (0.7 + difficulty * 0.1))   # Upper bound moves up
            )
        else:
            obstacle_height = 0

        color_variant = random.randint(0, 2)
        building_style = random.randint(0, 2)
        has_antenna = random.random() < 0.3  # 30% chance of antenna
        has_roof_detail = random.random() < 0.5  # 50% chance of roof details

        return Building(
            x=base_x,
            height=height,
            has_obstacle=has_obstacle,
            obstacle_height=obstacle_height,
            color_variant=color_variant,
            building_style=building_style,
            has_antenna=has_antenna,
            has_roof_detail=has_roof_detail
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

    def create_boost_effect(self):
        """Create visual effect when boost is activated"""
        spidy = self.spiderman
        # Create circular burst of particles
        for i in range(16):
            angle = (i / 16) * 2 * math.pi
            speed = random.uniform(3, 5)
            self.add_particle(
                spidy.x, spidy.y,
                speed * math.cos(angle), speed * math.sin(angle),
                random.choice(['⚡', '✨', '💨', '⭐']),
                13  # Purple/Magenta for boost
            )

    def activate_boost(self):
        """Activate boost to spin around anchor point"""
        if self.spiderman.boosts_remaining > 0 and self.boost_cooldown == 0 and self.spiderman.is_swinging:
            spidy = self.spiderman

            # Calculate current angle
            dx = spidy.x - spidy.swing_anchor_x
            dy = spidy.y - spidy.swing_anchor_y
            angle = math.atan2(dy, dx)

            # Add angular velocity boost (tangential direction)
            boost_strength = 8.0  # Strong boost!
            tangent_x = -math.sin(angle)
            tangent_y = math.cos(angle)

            # Apply boost in tangential direction
            spidy.vx += tangent_x * boost_strength
            spidy.vy += tangent_y * boost_strength

            # Consume boost
            spidy.boosts_remaining -= 1
            self.boost_cooldown = 10  # Frames before next boost

            # Visual feedback
            self.create_boost_effect()

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

        # Add new buildings with progressive difficulty
        if self.buildings:
            last_building = max(self.buildings, key=lambda b: b.x)
            while last_building.x < self.camera_x + self.width + 50:
                gap = self.get_building_gap(last_building.x)
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
            elif key in [ord('b'), ord('B')] and self.spiderman.is_swinging:
                # BOOST! Spin around anchor
                self.activate_boost()
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
        """Shoot web to the nearest building anchor point OR floating anchor"""
        if not self.spiderman.is_swinging:
            nearest = None
            min_distance = float('inf')

            # Get current difficulty for adaptive web range
            difficulty = self.get_difficulty_level(self.spiderman.x)
            web_range = MAX_ROPE_LENGTH + (1.0 - difficulty) * 15  # Extra range early on

            # Check building anchor points
            for building in self.buildings:
                for offset in [0.3, 0.5, 0.7]:
                    bldg_top_x = building.x + building.width * offset
                    bldg_top_y = self.height - building.height - 1

                    if bldg_top_x > self.spiderman.x - 5:
                        dx = bldg_top_x - self.spiderman.x
                        dy = bldg_top_y - self.spiderman.y
                        distance = math.sqrt(dx * dx + dy * dy)

                        if distance < web_range and distance < min_distance:
                            min_distance = distance
                            nearest = (bldg_top_x, bldg_top_y)

            # Check floating anchor points!
            for anchor in self.floating_anchors:
                if anchor.x > self.spiderman.x - 5:
                    dx = anchor.x - self.spiderman.x
                    dy = anchor.y - self.spiderman.y
                    distance = math.sqrt(dx * dx + dy * dy)

                    if distance < web_range and distance < min_distance:
                        min_distance = distance
                        nearest = (anchor.x, anchor.y)

            if nearest:
                self.spiderman.is_swinging = True
                self.spiderman.swing_anchor_x = nearest[0]
                self.spiderman.swing_anchor_y = nearest[1]
                self.spiderman.rope_length = min_distance
                self.create_web_particles()
                self.combo += 1
                self.max_combo = max(self.max_combo, self.combo)

    def update_physics(self):
        """Update game physics with slow-motion swing control"""
        if self.state != GameState.PLAYING:
            return

        spidy = self.spiderman
        self.frame_count += 1
        spidy.animation_frame = (spidy.animation_frame + 1) % 20

        # Update boost cooldown
        if self.boost_cooldown > 0:
            self.boost_cooldown -= 1

        if spidy.is_swinging:
            # Swinging physics with pendulum motion - MUCH MORE FORGIVING
            dx = spidy.x - spidy.swing_anchor_x
            dy = spidy.y - spidy.swing_anchor_y
            current_distance = math.sqrt(dx**2 + dy**2)

            if current_distance > 0.1:
                angle = math.atan2(dy, dx)

                # Constrain to rope length
                if current_distance > spidy.rope_length:
                    spidy.x = spidy.swing_anchor_x + spidy.rope_length * math.cos(angle)
                    spidy.y = spidy.swing_anchor_y + spidy.rope_length * math.sin(angle)

                    # Tangential velocity with MORE momentum preservation
                    tangent_x = -math.sin(angle)
                    tangent_y = math.cos(angle)

                    v_tangent = spidy.vx * tangent_x + spidy.vy * tangent_y

                    # Apply LESS gravity for easier control
                    gravity_component = GRAVITY * math.cos(angle)
                    v_tangent += gravity_component * 0.3  # Reduced from 0.5

                    # Update velocity with MORE boost
                    spidy.vx = v_tangent * tangent_x * 1.05  # Increased from 1.02
                    spidy.vy = v_tangent * tangent_y * 1.05

                # DISABLE auto-release - let player control it
                # if spidy.vy < -3 and dy < 0:
                #     spidy.is_swinging = False
                #     spidy.vy *= 1.1

            self.create_swing_trail()
        else:
            # Free fall - slower gravity
            spidy.vy += GRAVITY * 0.8  # Reduced gravity in free fall
            spidy.vx *= 0.99  # Less air resistance to maintain momentum
            self.combo = 0

        # Apply velocity - SLOWER when swinging for control
        velocity_multiplier = 0.7 if spidy.is_swinging else 1.0
        spidy.x += spidy.vx * velocity_multiplier
        spidy.y += spidy.vy * velocity_multiplier

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

        # Update floating anchors
        self.update_floating_anchors()

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
        """Draw ENHANCED game background with city atmosphere"""
        # Sky gradient with stars/atmosphere
        for y in range(0, self.height - 3):
            if y % 4 == 0:
                char = '·' if random.random() < 0.1 else ' '
                color = curses.color_pair(8)
                for x in range(0, self.width, 3):
                    try:
                        self.stdscr.addstr(y, x, char, color)
                    except:
                        pass

        # Draw enhanced ground/street at bottom
        ground_y = self.height - 2
        if ground_y >= 0:
            for x in range(0, self.width):
                try:
                    # Street pattern
                    if x % 10 == 0:
                        char = '║'  # Street markers
                        color = curses.color_pair(15)
                    elif x % 5 == 0:
                        char = '│'
                        color = curses.color_pair(9)
                    else:
                        char = '═'
                        color = curses.color_pair(9)

                    self.stdscr.addstr(ground_y, x, char, color)

                    # Ground level below
                    if ground_y + 1 < self.height:
                        self.stdscr.addstr(ground_y + 1, x, '▓',
                                         curses.color_pair(9) | curses.A_DIM)
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

        # Draw buildings with BLACK AND WHITE graphics
        for building in self.buildings:
            screen_x = int(building.x - self.camera_x)

            if -building.width <= screen_x <= self.width:
                bldg_top = self.height - building.height

                # Check if this building has the web attached to it (GLOW EFFECT!)
                is_web_attached = False
                if self.spiderman.is_swinging:
                    anchor_x = self.spiderman.swing_anchor_x
                    if building.x <= anchor_x <= building.x + building.width:
                        is_web_attached = True

                # Black and white color scheme - GLOW when web attached
                if is_web_attached:
                    fill_color = curses.color_pair(4)  # Yellow glow
                    edge_color = curses.color_pair(4)  # Yellow glow
                    window_color = curses.color_pair(4)  # Yellow glow
                else:
                    fill_color = curses.color_pair(9)  # White/gray
                    edge_color = curses.color_pair(9)  # White/gray
                    window_color = curses.color_pair(9)  # White/gray

                # Draw antenna on roof (if has_antenna)
                if building.has_antenna and bldg_top > 2:
                    antenna_x = screen_x + building.width // 2
                    if 0 <= antenna_x < self.width - 1:
                        # Antenna tower - simpler
                        for antenna_y in range(max(0, bldg_top - 3), bldg_top):
                            try:
                                if antenna_y == bldg_top - 3:
                                    self.stdscr.addstr(antenna_y, antenna_x, '^', edge_color | curses.A_BOLD)
                                else:
                                    self.stdscr.addstr(antenna_y, antenna_x, '|', edge_color)
                            except:
                                pass

                # Draw roof details (if has_roof_detail)
                if building.has_roof_detail and bldg_top >= 0:
                    for x in range(building.width):
                        draw_x = screen_x + x
                        if 0 <= draw_x < self.width - 1 and 0 <= bldg_top < self.height - 1:
                            try:
                                # Rooftop features - simpler
                                if building.building_style == 0:
                                    char = '▀' if x % 2 == 0 else '▄'
                                elif building.building_style == 1:
                                    char = '=' if x % 3 == 0 else '-'
                                else:
                                    char = '_'
                                attr = edge_color | curses.A_BOLD if is_web_attached else edge_color
                                self.stdscr.addstr(bldg_top, draw_x, char, attr)
                            except:
                                pass

                # Draw building body - SIMPLE BLACK AND WHITE
                for y in range(bldg_top + 1, self.height - 1):
                    for x in range(building.width):
                        draw_x = screen_x + x
                        if 0 <= draw_x < self.width - 1 and 0 <= y < self.height - 1:
                            # Simple building patterns
                            is_left_edge = (x == 0)
                            is_right_edge = (x == building.width - 1)
                            floor_num = (self.height - 1 - y)

                            # Simple window pattern
                            is_window = (x % 3 == 1 and floor_num % 4 == 2)

                            # Draw based on position
                            if is_left_edge or is_right_edge:
                                # Edges
                                char = '|'
                                attr = edge_color | curses.A_BOLD if is_web_attached else edge_color
                            elif is_window:
                                # Windows - simple
                                char = '#'
                                attr = window_color | curses.A_BOLD if is_web_attached else window_color
                            else:
                                # Building fill
                                char = '.'
                                attr = fill_color
                            try:
                                self.stdscr.addstr(y, draw_x, char, attr)
                            except:
                                pass

                # Draw obstacle - simple dangerous spikes
                if building.has_obstacle:
                    obstacle_y = self.height - building.obstacle_height
                    for x in range(1, building.width - 1):
                        draw_x = screen_x + x
                        if 0 <= draw_x < self.width - 1 and 0 <= obstacle_y < self.height - 1:
                            # Simple spikes - no blinking
                            char = 'v' if x % 2 == 0 else '^'
                            try:
                                self.stdscr.addstr(obstacle_y, draw_x, char,
                                                 curses.color_pair(6) | curses.A_BOLD)
                            except:
                                pass

        # Draw ENHANCED floating anchor points (flying platforms)
        for anchor in self.floating_anchors:
            anchor_x = int(anchor.x - self.camera_x)
            anchor_y = int(anchor.y)

            if 0 <= anchor_x < self.width - 1 and 0 <= anchor_y < self.height - 1:
                # Draw bigger cloud platform with layering
                platform_width = 5
                for offset in range(-platform_width // 2, platform_width // 2 + 1):
                    draw_x = anchor_x + offset
                    if 0 <= draw_x < self.width - 1:
                        try:
                            # Main cloud layer
                            if abs(offset) <= 1:
                                char = '☁'
                                color = curses.color_pair(anchor.color) | curses.A_BOLD
                            else:
                                char = '~'
                                color = curses.color_pair(anchor.color)

                            self.stdscr.addstr(anchor_y, draw_x, char, color)

                            # Shadow/edge layer below
                            if anchor_y + 1 < self.height - 1 and abs(offset) <= 2:
                                shadow_char = '·'
                                self.stdscr.addstr(anchor_y + 1, draw_x, shadow_char,
                                                 curses.color_pair(8) | curses.A_DIM)
                        except:
                            pass

        # Draw ENHANCED web rope with animated effects
        if self.spiderman.is_swinging:
            rope_x = int(self.spiderman.swing_anchor_x - self.camera_x)
            rope_y = int(self.spiderman.swing_anchor_y)
            spidy_x = int(self.spiderman.x - self.camera_x)
            spidy_y = int(self.spiderman.y)

            # Draw swing arc indicator (shows where you'll go) - ENHANCED
            rope_length = self.spiderman.rope_length
            for arc_step in range(0, 360, 20):  # More arc points
                arc_angle = math.radians(arc_step)
                arc_x = int(rope_x + rope_length * math.cos(arc_angle))
                arc_y = int(rope_y + rope_length * math.sin(arc_angle))

                if 0 <= arc_x < self.width - 1 and 0 <= arc_y < self.height - 1:
                    try:
                        # Pulsing arc indicator
                        char = '•' if arc_step % 40 == 0 else '·'
                        color = curses.color_pair(10) | curses.A_DIM
                        self.stdscr.addstr(arc_y, arc_x, char, color)
                    except:
                        pass

            # Calculate web line properties
            dx = spidy_x - rope_x
            dy = spidy_y - rope_y
            web_length = math.sqrt(dx*dx + dy*dy)
            steps = max(int(web_length * 2), abs(dx), abs(dy))  # More steps for smoother web

            # Draw web line - ANIMATED AND GLOWING
            if steps > 0:
                for i in range(steps):
                    t = i / steps
                    x = int(rope_x + dx * t)
                    y = int(rope_y + dy * t)

                    if 0 <= x < self.width - 1 and 0 <= y < self.height - 1:
                        # Advanced web pattern with animation
                        position_in_web = (i + self.frame_count) % 8

                        # Multi-layered web effect
                        if position_in_web < 2:
                            # Glowing segments
                            char = '═'
                            color = curses.color_pair(4) | curses.A_BOLD
                        elif i % 4 == 0:
                            # Strong web strands
                            char = '━'
                            color = curses.color_pair(4) | curses.A_BOLD
                        elif i % 4 == 1:
                            # Medium strands
                            char = '▬'
                            color = curses.color_pair(10)
                        elif i % 4 == 2:
                            # Light strands
                            char = '─'
                            color = curses.color_pair(10)
                        else:
                            # Web connectors
                            char = '┄'
                            color = curses.color_pair(4)

                        try:
                            self.stdscr.addstr(y, x, char, color)
                        except:
                            pass

                # Draw web thickness (parallel line for 3D effect)
                if dx != 0 and dy != 0:
                    offset_x = 1 if abs(dy) > abs(dx) else 0
                    offset_y = 1 if abs(dx) > abs(dy) else 0

                    for i in range(0, steps, 3):  # Draw every 3rd point on parallel line
                        t = i / steps
                        x = int(rope_x + dx * t) + offset_x
                        y = int(rope_y + dy * t) + offset_y

                        if 0 <= x < self.width - 1 and 0 <= y < self.height - 1:
                            try:
                                char = '·'
                                color = curses.color_pair(10) | curses.A_DIM
                                self.stdscr.addstr(y, x, char, color)
                            except:
                                pass

            # Draw anchor point - ENHANCED with glow
            if 0 <= rope_x < self.width - 1 and 0 <= rope_y < self.height - 1:
                # Anchor glow effect
                for glow_offset_x in [-1, 0, 1]:
                    for glow_offset_y in [-1, 0, 1]:
                        glow_x = rope_x + glow_offset_x
                        glow_y = rope_y + glow_offset_y
                        if 0 <= glow_x < self.width - 1 and 0 <= glow_y < self.height - 1:
                            try:
                                if glow_offset_x == 0 and glow_offset_y == 0:
                                    # Center anchor
                                    self.stdscr.addstr(glow_y, glow_x, '⚓',
                                                     curses.color_pair(4) | curses.A_BOLD)
                                else:
                                    # Glow around anchor
                                    char = '·' if (self.frame_count + glow_offset_x + glow_offset_y) % 3 == 0 else ' '
                                    if char == '·':
                                        self.stdscr.addstr(glow_y, glow_x, char,
                                                         curses.color_pair(10) | curses.A_DIM)
                            except:
                                pass

        # Draw Spiderman - BETTER CHARACTER
        spidy_screen_x = int(self.spiderman.x - self.camera_x)
        spidy_screen_y = int(self.spiderman.y)

        if 0 <= spidy_screen_x < self.width - 1 and 0 <= spidy_screen_y < self.height - 1:
            # Better Spiderman character
            if self.spiderman.is_swinging:
                # Swinging pose - use @ for body
                spidy_char = '@'
            else:
                # Falling pose
                spidy_char = 'O'

            try:
                self.stdscr.addstr(spidy_screen_y, spidy_screen_x, spidy_char,
                                 curses.color_pair(1) | curses.A_BOLD)
            except:
                pass

        # Draw HUD
        self.draw_hud()

    def draw_hud(self):
        """Draw ENHANCED heads-up display with borders"""
        try:
            # Calculate stats
            speed = math.sqrt(self.spiderman.vx**2 + self.spiderman.vy**2)
            difficulty = self.get_difficulty_level(self.spiderman.x)
            difficulty_pct = int(difficulty * 100)

            # ===== TOP LEFT HUD BOX =====
            hud_lines = []
            hud_lines.append(f"╔═══════════════════════╗")
            hud_lines.append(f"║ Score: {self.score:<13} ║")
            hud_lines.append(f"║ Speed: {speed:<13.1f} ║")

            if difficulty_pct > 0:
                hud_lines.append(f"║ Diff: {difficulty_pct:>3}%           ║")

            if self.spiderman.boosts_remaining > 0:
                boosts_display = f"{self.spiderman.boosts_remaining}/10"
                hud_lines.append(f"║ Boosts: {boosts_display:<12} ║")

            hud_lines.append(f"╚═══════════════════════╝")

            # Draw HUD box
            for i, line in enumerate(hud_lines):
                try:
                    if i == 0 or i == len(hud_lines) - 1:
                        # Border lines
                        color = curses.color_pair(4) | curses.A_BOLD
                    elif "Score" in line:
                        color = curses.color_pair(12) | curses.A_BOLD
                    elif "Speed" in line:
                        color = curses.color_pair(5)
                    elif "Diff" in line:
                        color = curses.color_pair(5) if difficulty < 0.5 else curses.color_pair(7) if difficulty < 0.8 else curses.color_pair(6)
                        color |= curses.A_BOLD
                    elif "Boosts" in line:
                        color = curses.color_pair(13) | curses.A_BOLD
                        if self.spiderman.boosts_remaining <= 3:
                            color |= curses.A_BLINK
                    else:
                        color = curses.color_pair(9)

                    self.stdscr.addstr(i, 1, line, color)
                except:
                    pass

            # ===== COMBO DISPLAY (if active) =====
            if self.combo > 1:
                combo_y = len(hud_lines) + 1
                combo_text = f"╔═══════════════════════╗"
                combo_val = f"║  COMBO x{self.combo}!        ║"
                combo_bot = f"╚═══════════════════════╝"

                combo_color = curses.color_pair(7) | curses.A_BOLD

                try:
                    self.stdscr.addstr(combo_y, 1, combo_text, curses.color_pair(7))
                    self.stdscr.addstr(combo_y + 1, 1, combo_val, combo_color)
                    self.stdscr.addstr(combo_y + 2, 1, combo_bot, curses.color_pair(7))
                except:
                    pass

            # ===== TOP RIGHT STATUS BOX =====
            status_lines = []
            status_lines.append(f"╔══════════════╗")

            if self.spiderman.is_swinging:
                status_lines.append(f"║  SLOW-MO     ║")
                status_lines.append(f"║  SWINGING!   ║")
                status_color = curses.color_pair(4)
            else:
                status_lines.append(f"║              ║")
                status_lines.append(f"║  FREE FALL   ║")
                status_color = curses.color_pair(6)

            status_lines.append(f"╚══════════════╝")

            # Draw status box (top right)
            status_x = self.width - 18
            for i, line in enumerate(status_lines):
                try:
                    if i == 0 or i == len(status_lines) - 1:
                        color = curses.color_pair(4)
                    else:
                        color = status_color | curses.A_BOLD

                    self.stdscr.addstr(i, status_x, line, color)
                except:
                    pass

            # ===== TUTORIAL MESSAGES =====
            if self.spiderman.x < 250:
                tutorial_y = self.height - 7  # Bottom of screen, above controls

                # Determine message
                if self.spiderman.x < 80:
                    tutorial_msg = "Already swinging! Press [B] for BOOST to spin faster!"
                elif self.spiderman.x < 150:
                    tutorial_msg = "Time SLOWS when swinging! Press [B] to BOOST!"
                elif self.spiderman.x < 200:
                    tutorial_msg = "Chain swings to build combos! Game gets harder!"
                elif self.spiderman.x < 250:
                    tutorial_msg = "Use [B] BOOST when swing slows - you have 10 per game!"
                else:
                    tutorial_msg = ""

                # Draw tutorial box
                if tutorial_msg:
                    box_width = len(tutorial_msg) + 4
                    x = max(0, (self.width - box_width) // 2)

                    try:
                        top_border = "╔" + "═" * (box_width - 2) + "╗"
                        msg_line = f"║ {tutorial_msg} ║"
                        bot_border = "╚" + "═" * (box_width - 2) + "╝"

                        self.stdscr.addstr(tutorial_y, x, top_border, curses.color_pair(5))
                        self.stdscr.addstr(tutorial_y + 1, x, msg_line,
                                         curses.color_pair(5) | curses.A_BOLD)
                        self.stdscr.addstr(tutorial_y + 2, x, bot_border, curses.color_pair(5))
                    except:
                        pass

            # ===== BOTTOM CONTROLS BAR =====
            controls_line = "╔════════════════════════════════════════════════════════════╗"
            controls_text = "║ [SPACE] Web  │  [B] Boost  │  [P] Pause  │  [Q] Quit     ║"
            controls_bot  = "╚════════════════════════════════════════════════════════════╝"

            try:
                bottom_y = self.height - 3
                self.stdscr.addstr(bottom_y, 1, controls_line, curses.color_pair(9))
                self.stdscr.addstr(bottom_y + 1, 1, controls_text, curses.color_pair(9))
                self.stdscr.addstr(bottom_y + 2, 1, controls_bot, curses.color_pair(9))
            except:
                pass

        except:
            pass

    def run(self):
        """Main game loop with adaptive speed"""
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

            # SLOW MOTION when swinging for better control!
            if self.state == GameState.PLAYING and self.spiderman and self.spiderman.is_swinging:
                time.sleep(SWING_SLOWMO_SPEED)
            else:
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
