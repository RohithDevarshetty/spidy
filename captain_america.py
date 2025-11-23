#!/usr/bin/env python3
"""
Captain America: Shield Assault - A Terminal-Based Action Game
Throw your shield, defeat HYDRA agents, and save the day!
"""

import curses
import random
import math
import time
import os
from dataclasses import dataclass
from typing import List
from enum import Enum

# Game Constants
GRAVITY = 0.4
JUMP_STRENGTH = -8.0
MOVE_SPEED = 1.5
SHIELD_SPEED = 15.0
SHIELD_RETURN_SPEED = 12.0
GAME_SPEED = 0.04
PARTICLE_LIFETIME = 10
MAX_PARTICLES = 30


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
class CaptainAmerica:
    x: float
    y: float
    vx: float = 0
    vy: float = 0
    is_jumping: bool = False
    facing_right: bool = True
    animation_frame: int = 0


@dataclass
class Shield:
    x: float
    y: float
    vx: float
    vy: float
    is_thrown: bool = False
    is_returning: bool = False
    hits: int = 0  # Number of enemies hit in this throw


@dataclass
class Enemy:
    x: float
    y: float
    vx: float = -1.0
    health: int = 1
    enemy_type: int = 0  # 0=soldier, 1=shield bearer


class CaptainAmericaGame:
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
        self.wave = 1

        # Initialize curses
        curses.curs_set(0)
        stdscr.nodelay(1)
        stdscr.timeout(30)

        try:
            curses.use_default_colors()
        except:
            pass

        self._init_colors()

        self.captain = None
        self.shield = None
        self.enemies: List[Enemy] = []
        self.particles: List[Particle] = []
        self.frame_count = 0
        self.spawn_timer = 0
        self.ground_level = self.height - 5

    def _check_terminal(self) -> bool:
        """Check if terminal supports required features"""
        try:
            if 'TERM' not in os.environ or os.environ['TERM'] == 'unknown':
                os.environ['TERM'] = 'xterm-256color'
            return True
        except:
            return False

    def _init_colors(self):
        """Initialize color pairs"""
        curses.start_color()

        try:
            if curses.can_change_color() and curses.COLORS >= 256:
                curses.init_pair(1, 21, -1)     # Blue - Captain America
                curses.init_pair(2, 196, -1)    # Red - Shield
                curses.init_pair(3, 9, -1)      # Gray - Enemies
                curses.init_pair(4, 226, -1)    # Yellow - Effects
                curses.init_pair(5, 46, -1)     # Green - Score
                curses.init_pair(6, 196, -1)    # Red - Damage
                curses.init_pair(7, 202, -1)    # Orange - Combo
                curses.init_pair(8, 27, -1)     # Blue - Sky
                curses.init_pair(9, 240, -1)    # Gray - UI
            else:
                raise Exception("Fallback to 8 colors")
        except:
            curses.init_pair(1, curses.COLOR_BLUE, -1)
            curses.init_pair(2, curses.COLOR_RED, -1)
            curses.init_pair(3, curses.COLOR_WHITE, -1)
            curses.init_pair(4, curses.COLOR_YELLOW, -1)
            curses.init_pair(5, curses.COLOR_GREEN, -1)
            curses.init_pair(6, curses.COLOR_RED, -1)
            curses.init_pair(7, curses.COLOR_YELLOW, -1)
            curses.init_pair(8, curses.COLOR_BLUE, -1)
            curses.init_pair(9, curses.COLOR_WHITE, -1)

    def init_game(self):
        """Initialize a new game"""
        self.state = GameState.PLAYING
        self.score = 0
        self.combo = 0
        self.wave = 1
        self.spawn_timer = 0

        # Create Captain America at left side
        self.captain = CaptainAmerica(
            x=20,
            y=self.ground_level
        )

        # Create shield (not thrown initially)
        self.shield = Shield(
            x=self.captain.x,
            y=self.captain.y,
            vx=0,
            vy=0
        )

        self.enemies = []
        self.particles = []
        self.frame_count = 0

    def add_particle(self, x: float, y: float, vx: float, vy: float, char: str, color: int):
        """Add a particle effect"""
        if len(self.particles) < MAX_PARTICLES:
            self.particles.append(Particle(x, y, vx, vy, char, color, PARTICLE_LIFETIME))

    def create_hit_effect(self, x: float, y: float):
        """Create explosion effect when shield hits enemy"""
        for i in range(8):
            angle = (i / 8) * 2 * math.pi
            speed = random.uniform(2, 4)
            self.add_particle(
                x, y,
                speed * math.cos(angle), speed * math.sin(angle),
                random.choice(['*', '+', 'x']),
                4  # Yellow
            )

    def create_shield_trail(self):
        """Create trail particles for shield"""
        if random.random() < 0.5 and self.shield.is_thrown:
            self.add_particle(
                self.shield.x, self.shield.y,
                self.shield.vx * 0.2, self.shield.vy * 0.2,
                random.choice(['-', '=', '~']),
                2  # Red
            )

    def update_particles(self):
        """Update all particle positions and lifetimes"""
        for particle in self.particles:
            particle.x += particle.vx
            particle.y += particle.vy
            particle.vy += 0.15  # Gravity
            particle.vx *= 0.95  # Air resistance
            particle.lifetime -= 1

        # Remove dead particles
        self.particles = [p for p in self.particles if p.lifetime > 0]

    def spawn_enemy(self):
        """Spawn a new enemy"""
        enemy_type = random.randint(0, 1) if self.wave > 3 else 0
        self.enemies.append(Enemy(
            x=self.width - 5,
            y=self.ground_level,
            vx=-1.0 - (self.wave * 0.1),  # Speed increases with waves
            enemy_type=enemy_type
        ))

    def throw_shield(self):
        """Throw the shield"""
        if not self.shield.is_thrown and not self.shield.is_returning:
            self.shield.is_thrown = True
            self.shield.is_returning = False
            self.shield.hits = 0
            self.shield.x = self.captain.x
            self.shield.y = self.captain.y - 1

            # Throw in facing direction
            direction = 1 if self.captain.facing_right else -1
            self.shield.vx = SHIELD_SPEED * direction
            self.shield.vy = -2.0  # Slight upward arc

    def handle_input(self, key):
        """Handle keyboard input"""
        if self.state == GameState.MENU:
            if key in [ord('s'), ord('S'), ord(' ')]:
                self.init_game()
            elif key == ord('q'):
                return False

        elif self.state == GameState.PLAYING:
            cap = self.captain

            # Movement
            if key in [curses.KEY_LEFT, ord('a'), ord('A')]:
                cap.vx = -MOVE_SPEED
                cap.facing_right = False
            elif key in [curses.KEY_RIGHT, ord('d'), ord('D')]:
                cap.vx = MOVE_SPEED
                cap.facing_right = True

            # Jump
            if key in [curses.KEY_UP, ord('w'), ord('W'), ord(' ')]:
                if not cap.is_jumping:
                    cap.vy = JUMP_STRENGTH
                    cap.is_jumping = True

            # Throw shield
            if key in [ord('f'), ord('F'), ord('e'), ord('E')]:
                self.throw_shield()

            # Pause
            if key == ord('p'):
                self.state = GameState.PAUSED

            # Quit
            if key == ord('q'):
                self.state = GameState.MENU

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

    def update_physics(self):
        """Update game physics"""
        if self.state != GameState.PLAYING:
            return

        cap = self.captain
        self.frame_count += 1
        cap.animation_frame = (cap.animation_frame + 1) % 20

        # Captain physics
        cap.vy += GRAVITY
        cap.x += cap.vx
        cap.y += cap.vy

        # Ground collision
        if cap.y >= self.ground_level:
            cap.y = self.ground_level
            cap.vy = 0
            cap.is_jumping = False

        # Boundary check
        cap.x = max(5, min(cap.x, self.width - 10))

        # Friction
        cap.vx *= 0.8

        # Shield physics
        shield = self.shield
        if shield.is_thrown:
            shield.x += shield.vx
            shield.y += shield.vy
            shield.vy += 0.2  # Slight gravity on shield

            # Check if shield should return
            distance_from_captain = abs(shield.x - cap.x)
            if distance_from_captain > 40 or shield.x < 0 or shield.x > self.width:
                shield.is_returning = True
                shield.is_thrown = False

            self.create_shield_trail()

        elif shield.is_returning:
            # Shield returns to captain
            dx = cap.x - shield.x
            dy = (cap.y - 1) - shield.y
            distance = math.sqrt(dx*dx + dy*dy)

            if distance < 3:
                # Caught the shield!
                shield.is_returning = False
                shield.x = cap.x
                shield.y = cap.y

                # Award combo bonus
                if shield.hits > 0:
                    self.score += shield.hits * 50
                    self.combo = shield.hits
                    self.max_combo = max(self.max_combo, self.combo)
            else:
                # Move shield towards captain
                shield.vx = (dx / distance) * SHIELD_RETURN_SPEED
                shield.vy = (dy / distance) * SHIELD_RETURN_SPEED
                shield.x += shield.vx
                shield.y += shield.vy

            self.create_shield_trail()
        else:
            # Shield follows captain
            shield.x = cap.x
            shield.y = cap.y

        # Update enemies
        for enemy in self.enemies:
            enemy.x += enemy.vx

        # Remove off-screen enemies
        self.enemies = [e for e in self.enemies if e.x > -10]

        # Spawn enemies
        self.spawn_timer += 1
        spawn_rate = max(30, 100 - self.wave * 5)
        if self.spawn_timer > spawn_rate and len(self.enemies) < 10:
            self.spawn_enemy()
            self.spawn_timer = 0

        # Check collisions
        self.check_collisions()

        # Update particles
        self.update_particles()

    def check_collisions(self):
        """Check for collisions"""
        shield = self.shield

        # Shield vs Enemies
        if shield.is_thrown or shield.is_returning:
            for enemy in self.enemies[:]:
                dx = shield.x - enemy.x
                dy = shield.y - enemy.y
                distance = math.sqrt(dx*dx + dy*dy)

                if distance < 3:
                    # Hit!
                    enemy.health -= 1
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)
                        self.score += 100
                        shield.hits += 1
                        self.create_hit_effect(enemy.x, enemy.y)

        # Captain vs Enemies
        cap = self.captain
        for enemy in self.enemies:
            dx = cap.x - enemy.x
            dy = cap.y - enemy.y
            distance = math.sqrt(dx*dx + dy*dy)

            if distance < 2:
                # Game over!
                self.game_over()
                return

    def game_over(self):
        """Handle game over"""
        self.state = GameState.GAME_OVER
        self.high_score = max(self.high_score, self.score)

    def draw_menu(self):
        """Draw the main menu"""
        self.stdscr.clear()

        title = [
            "  ╔═══════════════════════════════════════════════════════════╗",
            "  ║                                                           ║",
            "  ║     CAPTAIN AMERICA: SHIELD ASSAULT                       ║",
            "  ║                                                           ║",
            "  ╚═══════════════════════════════════════════════════════════╝",
        ]

        start_y = max(2, self.height // 2 - 10)

        for i, line in enumerate(title):
            if start_y + i < self.height - 1:
                x = max(0, (self.width - len(line)) // 2)
                color = curses.color_pair(1) | curses.A_BOLD
                try:
                    self.stdscr.addstr(start_y + i, min(x, self.width - 2),
                                     line[:self.width-1], color)
                except:
                    pass

        instructions = [
            "",
            "CONTROLS:",
            "  [A/D] or [Arrows] - Move Left/Right",
            "  [W] or [Up] - Jump",
            "  [F] or [E] - Throw Shield",
            "  [P] - Pause",
            "  [Q] - Quit",
            "",
            "OBJECTIVE:",
            "  Defeat HYDRA agents with your shield!",
            "  Hit multiple enemies for combo bonuses!",
            "  Don't let enemies reach you!",
            "",
            "Press [SPACE] to start!",
        ]

        for i, line in enumerate(instructions):
            y = start_y + len(title) + i + 2
            if y < self.height - 1:
                x = max(0, (self.width - len(line)) // 2)
                if "SPACE" in line:
                    color = curses.color_pair(5) | curses.A_BOLD
                else:
                    color = curses.color_pair(9)
                try:
                    self.stdscr.addstr(y, min(x, self.width - 2),
                                     line[:self.width-1], color)
                except:
                    pass

        if self.high_score > 0:
            score_text = f"HIGH SCORE: {self.high_score}"
            try:
                y = self.height - 3
                x = max(0, (self.width - len(score_text)) // 2)
                self.stdscr.addstr(y, min(x, self.width - 2),
                                 score_text[:self.width-1],
                                 curses.color_pair(5) | curses.A_BOLD)
            except:
                pass

    def draw_game_over(self):
        """Draw game over screen"""
        self.stdscr.clear()

        # Draw faded game state
        self.draw_game_background()

        # Game over overlay
        game_over_text = [
            "╔═══════════════════════════════════╗",
            "║        MISSION FAILED             ║",
            "╚═══════════════════════════════════╝",
        ]

        start_y = max(2, self.height // 2 - 8)

        for i, line in enumerate(game_over_text):
            y = start_y + i
            if 0 <= y < self.height - 1:
                x = max(0, (self.width - len(line)) // 2)
                try:
                    self.stdscr.addstr(y, min(x, self.width - 2),
                                     line[:self.width-1],
                                     curses.color_pair(6) | curses.A_BOLD)
                except:
                    pass

        # Stats
        stats = [
            f"",
            f"Score: {self.score}",
            f"High Score: {self.high_score}",
            f"Max Combo: x{self.max_combo}",
            f"Wave Reached: {self.wave}",
            "",
            "[SPACE] Try Again    [Q] Main Menu",
        ]

        for i, line in enumerate(stats):
            y = start_y + len(game_over_text) + i + 1
            if 0 <= y < self.height - 1:
                x = max(0, (self.width - len(line)) // 2)
                color = curses.color_pair(5) if "Score" in line or "Combo" in line or "Wave" in line else curses.color_pair(9)
                try:
                    self.stdscr.addstr(y, min(x, self.width - 2),
                                     line[:self.width-1], color | curses.A_BOLD)
                except:
                    pass

    def draw_game_background(self):
        """Draw game background"""
        # Sky
        for y in range(0, self.ground_level):
            if y % 5 == 0:
                char = '.' if random.random() < 0.05 else ' '
                color = curses.color_pair(8)
                for x in range(0, self.width, 4):
                    try:
                        self.stdscr.addstr(y, x, char, color)
                    except:
                        pass

        # Ground
        for x in range(0, self.width):
            try:
                if x % 10 == 0:
                    char = '|'
                else:
                    char = '='
                self.stdscr.addstr(self.ground_level + 1, x, char, curses.color_pair(9))
                self.stdscr.addstr(self.ground_level + 2, x, '#', curses.color_pair(9) | curses.A_DIM)
            except:
                pass

    def draw_game(self):
        """Draw the game state"""
        self.stdscr.clear()

        # Draw background
        self.draw_game_background()

        # Draw particles
        for particle in self.particles:
            screen_x = int(particle.x)
            screen_y = int(particle.y)
            if 0 <= screen_x < self.width - 1 and 0 <= screen_y < self.height - 1:
                alpha = particle.lifetime / PARTICLE_LIFETIME
                if alpha > 0.2:
                    try:
                        attr = curses.color_pair(particle.color)
                        if alpha > 0.6:
                            attr |= curses.A_BOLD
                        self.stdscr.addstr(screen_y, screen_x, particle.char, attr)
                    except:
                        pass

        # Draw enemies
        for enemy in self.enemies:
            x = int(enemy.x)
            y = int(enemy.y)
            if 0 <= x < self.width - 1 and 0 <= y < self.height - 1:
                if enemy.enemy_type == 0:
                    # Soldier
                    char = 'H'  # HYDRA
                else:
                    # Shield bearer
                    char = 'S'
                try:
                    self.stdscr.addstr(y, x, char, curses.color_pair(3) | curses.A_BOLD)
                except:
                    pass

        # Draw shield
        if self.shield:
            x = int(self.shield.x)
            y = int(self.shield.y)
            if 0 <= x < self.width - 1 and 0 <= y < self.height - 1:
                try:
                    self.stdscr.addstr(y, x, 'O', curses.color_pair(2) | curses.A_BOLD)
                except:
                    pass

        # Draw Captain America
        if self.captain:
            x = int(self.captain.x)
            y = int(self.captain.y)
            if 0 <= x < self.width - 1 and 0 <= y < self.height - 1:
                # Captain character
                if self.captain.is_jumping:
                    char = '^'
                else:
                    char = '@'

                try:
                    self.stdscr.addstr(y, x, char, curses.color_pair(1) | curses.A_BOLD)
                except:
                    pass

        # Draw HUD
        self.draw_hud()

    def draw_hud(self):
        """Draw heads-up display"""
        try:
            # Top left - Score
            hud_lines = []
            hud_lines.append("╔═══════════════════╗")
            hud_lines.append(f"║ Score: {self.score:<9} ║")
            hud_lines.append(f"║ Wave: {self.wave:<10} ║")
            hud_lines.append("╚═══════════════════╝")

            for i, line in enumerate(hud_lines):
                try:
                    if i == 0 or i == len(hud_lines) - 1:
                        color = curses.color_pair(1) | curses.A_BOLD
                    else:
                        color = curses.color_pair(5) | curses.A_BOLD
                    self.stdscr.addstr(i, 1, line, color)
                except:
                    pass

            # Combo display
            if self.combo > 0 and (self.shield.is_thrown or self.shield.is_returning):
                combo_y = len(hud_lines) + 1
                combo_text = f"╔═══════════════════╗"
                combo_val = f"║ COMBO x{self.combo}!      ║"
                combo_bot = f"╚═══════════════════╝"

                try:
                    self.stdscr.addstr(combo_y, 1, combo_text, curses.color_pair(7))
                    self.stdscr.addstr(combo_y + 1, 1, combo_val, curses.color_pair(7) | curses.A_BOLD)
                    self.stdscr.addstr(combo_y + 2, 1, combo_bot, curses.color_pair(7))
                except:
                    pass

            # Shield status
            shield_status = "READY"
            if self.shield.is_thrown:
                shield_status = "THROWN"
            elif self.shield.is_returning:
                shield_status = "RETURNING"

            status_x = self.width - 20
            status_lines = []
            status_lines.append("╔══════════════╗")
            status_lines.append(f"║ Shield:      ║")
            status_lines.append(f"║ {shield_status:<12} ║")
            status_lines.append("╚══════════════╝")

            for i, line in enumerate(status_lines):
                try:
                    color = curses.color_pair(2) if i in [1, 2] else curses.color_pair(9)
                    if i in [1, 2]:
                        color |= curses.A_BOLD
                    self.stdscr.addstr(i, status_x, line, color)
                except:
                    pass

            # Bottom controls
            controls = "[A/D] Move  [W] Jump  [F] Shield  [P] Pause  [Q] Quit"
            try:
                self.stdscr.addstr(self.height - 1, 2, controls, curses.color_pair(9))
            except:
                pass

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
                    pause_text = "PAUSED - Press [P] to continue"
                    y = self.height // 2
                    x = max(0, (self.width - len(pause_text)) // 2)
                    self.stdscr.addstr(y, x, pause_text,
                                     curses.color_pair(4) | curses.A_BOLD)

                self.stdscr.refresh()
            except:
                pass

            time.sleep(GAME_SPEED)


def main(stdscr):
    """Main entry point"""
    try:
        game = CaptainAmericaGame(stdscr)
        game.run()
    except Exception as e:
        curses.endwin()
        print(f"\n❌ Error running game: {e}")
        print("\n💡 Make sure you're running this in a proper terminal window.")
        raise


def main_wrapper():
    """Wrapper for console script entry point"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ['--version', '-v']:
        print("Captain America: Shield Assault v1.0.0")
        print("A terminal-based action game!")
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("🛡️  Captain America: Shield Assault")
        print("\nUsage: cap")
        print("\nControls:")
        print("  A/D or Arrows - Move")
        print("  W or Up - Jump")
        print("  F or E - Throw Shield")
        print("  P - Pause")
        print("  Q - Quit")
        print("\nObjective: Defeat HYDRA agents with your shield!")
        sys.exit(0)

    if 'TERM' not in os.environ or os.environ['TERM'] == 'unknown':
        os.environ['TERM'] = 'xterm-256color'

    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\n\n👋 Mission complete! See you next time, Captain!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main_wrapper()
