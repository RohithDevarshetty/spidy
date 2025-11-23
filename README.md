# 🕷️ Spidy - Spiderman Swinging Game

A thrilling terminal-based Spiderman swinging game with amazing ASCII graphics! Swing through the cityscape, avoid obstacles, and rack up high scores in this action-packed command-line adventure.

```
  _____ ____ _____ ____  _____ ____  __  __    _    _   _
 / ____|  _ \_   _|  _ \| ____|  _ \|  \/  |  / \  | \ | |
 \___ \| |_) || | | | | |  _| | |_) | |\/| | / _ \ |  \| |
  ___) |  __/ | | | |_| | |___|  _ <| |  | |/ ___ \| |\  |
 |____/|_|   |_| |____/|_____|_| \_\_|  |_/_/   \_\_| \_|

                    SWING THROUGH THE CITY!
```

## ✨ Features

- **🎨 Crazy Graphics**: 15+ color combinations with 256-color terminal support
- **💫 Particle Effects**: Web shooting particles, swing trails, and explosion effects
- **⏱️ SLOW-MOTION SWINGING**: Time slows down when you're swinging for precise control!
- **⚡ BOOST SYSTEM**: Press [B] to spin around anchor and build momentum - 10 boosts per game!
- **🎬 EPIC INTRO**: Game starts mid-swing from a building window - instant action!
- **☁️ FLYING PLATFORMS**: Swing to floating cloud anchors in the sky!
- **🏢 HUGE BUILDINGS**: Start with tall buildings (15-25 units) for better swinging
- **🌆 50 BUILDINGS**: Massive city with 50 buildings to swing through
- **🎯 Forgiving Physics**: Easy-to-learn swinging mechanics with visual arc indicators
- **📈 Progressive Difficulty**: Starts easy, gets harder as you play - perfect learning curve!
- **🎓 Tutorial Zone**: MASSIVE starting platform (60 units wide, 60% screen height!)
- **🏗️ Dynamic City Generation**: Procedurally generated buildings with unique designs
- **🔥 Combo System**: Chain swings together to build massive combos
- **⚡ Animated Character**: Spiderman changes appearance while swinging
- **🎪 Enhanced Buildings**: Multiple color variants, windows, and detailed architecture
- **💥 Obstacle Challenges**: Blinking hazards that gradually appear as difficulty increases
- **🏆 High Score Tracking**: Beat your personal records
- **⏸️ Pause Feature**: Take a break anytime
- **🎬 Smooth Gameplay**: Adaptive speed for maximum control

## 🎮 Gameplay

You are Spiderman, swinging through a bustling city. Your goal is to travel as far as possible without hitting the ground or crashing into obstacles!

### Controls

- `SPACE` - Shoot web and swing / Release web early for boost
- `B` - **BOOST** while swinging to spin around anchor and build momentum!
- `P` - Pause game
- `Q` - Quit to menu / Exit game
- `R` - Restart (when game over)

### Tips

1. **🎬 EPIC START**: Game begins mid-swing from the starting building - you're already in action!
2. **⚡ BOOST WHEN SLOW**: Press [B] when your swing slows down to spin faster around the anchor!
3. **⏱️ USE SLOW-MOTION**: When swinging, time SLOWS DOWN - use this to plan your release!
4. **💥 SAVE BOOSTS**: You only get 10 boosts per game - use them wisely!
5. **☁️ USE FLYING PLATFORMS**: Swing to cloud anchors (☁☁☁) when no buildings are nearby!
6. **🏢 BIGGER IS BETTER**: Tall buildings give you more swinging options
7. **👀 Watch the Arc**: Dotted circle shows your swing path - use it to aim your release
8. **🔥 Build Combos**: Chain swings together without touching ground to rack up combos
9. **⚡ Manual Release**: Press SPACE while swinging to release early and control your trajectory
10. **🎯 Auto-Aim**: Game finds the best anchor point (buildings OR clouds) automatically
11. **📊 Watch Difficulty**: Monitor the difficulty % - it increases gradually
12. **🏃 Momentum is Key**: Keep speed high by releasing at the right angle

## 🚀 Installation

### Via Homebrew (macOS)

The easiest way to install on macOS:

```bash
# Add the tap (repository)
brew tap RohithDevarshetty/spidy

# Install the game
brew install spidy

# Run the game
spidy
```

### From Source

If you want to install from source:

```bash
# Clone the repository
git clone https://github.com/RohithDevarshetty/spidy.git
cd spidy

# Install using pip
pip install .

# Or run directly with Python
python3 spiderman_swing.py
```

## 📋 Requirements

- **Python 3.7+**
- **Terminal with color support**
- **Recommended terminal size**: 120x40 or larger for best experience

The game uses Python's built-in `curses` library, which is included with Python on macOS and Linux. No additional dependencies required!

## 🎯 Game Mechanics

### Swinging Physics & Slow-Motion Control

The game implements **forgiving** pendulum physics with a unique slow-motion mechanic:

**Slow-Motion Swinging:**
- ⏱️ **Time slows by 50%** when you're swinging
- 🎯 Visual arc indicator shows your swing path
- 💭 Gives you time to plan your next move
- ⚡ Press SPACE to release and return to normal speed

**Boost System:**
- ⚡ **10 boosts per game** - use them strategically!
- 🌀 Press [B] while swinging to spin around anchor
- 💨 Adds 8.0 units of angular velocity in tangential direction
- ✨ Creates particle burst effect (⚡✨💨⭐)
- 🔄 10-frame cooldown between boosts (prevents spam)
- 📊 Counter shows remaining boosts (blinks when ≤3)
- 💡 Perfect for when your swing slows down!

**Physics:**
- Reduced gravity (0.25) for easier control
- Web acts as a rope with fixed length
- Momentum is boosted while swinging (+5% per swing)
- 70% velocity multiplier while swinging for precise control
- Less air resistance to maintain momentum
- NO auto-release - you control everything!

### Scoring & Combos

- **Distance Score**: Points increase as you travel further through the city
- **Combo System**: Each consecutive swing increases your combo multiplier
- **Max Combo Tracking**: See your longest swing chain in the game over screen
- **High Scores**: Your best run is saved and displayed on the menu

### Progressive Difficulty System

The game features a smart difficulty curve that adapts as you play:

**Tutorial Zone (0-100 units)**
- **AUTO-SWING START**: Game begins mid-swing from starting building window!
- MASSIVE starting platform (60 units wide, 60% of screen height!)
- Tall buildings right from the start (15-25 units tall) - proper swinging!
- Buildings close together (8-12 gap)
- **NO obstacles** - completely safe learning area
- Extended web range (up to 45 units) for easier swinging
- **SLOW-MOTION** activates when swinging for practice
- **30 FLOATING PLATFORMS** scattered throughout for aerial swinging!

**Easy (100-400 units, 0-20% difficulty)**
- Medium-tall buildings (15-25 units)
- Close gaps (8-12 units)
- Still no obstacles
- Longer web range
- Flying platforms available

**Medium (400-1000 units, 20-60% difficulty)**
- Tall buildings (20-30 units)
- Wider gaps (10-20 units)
- Obstacles start appearing (5-15% chance)
- Normal web range
- More flying platforms appear

**Hard (1000+ units, 60-100% difficulty)**
- Very tall buildings (25-35 units)
- Wide gaps (15-25 units)
- Many obstacles (15-30% chance)
- Standard web range
- Obstacles placed strategically
- Flying platforms essential for gap crossing

### Obstacles

- Appear gradually as difficulty increases
- Marked with blinking `▼` symbols in magenta
- Colliding with an obstacle ends the game
- Become more common at higher difficulties

## 🎨 Graphics & Visual Effects

Despite being a terminal game, Spidy features cutting-edge ASCII graphics:
- **15 Vibrant Colors**: Full 256-color terminal support with fallback to 8 colors
- **Particle System**: Real-time particle effects for webs, trails, and explosions
- **Animated Spiderman**: Character cycles through 4 animation frames (🕷⚡💫✨)
- **Building Variants**: 3 different color schemes with detailed windows and patterns
- **Dynamic Camera**: Smooth following with parallax-style scrolling
- **Blinking Effects**: Animated obstacles and UI elements
- **HUD System**: Real-time stats including score, speed, combo counter, and status
- **Beautiful Menus**: Unicode box-drawing characters and ASCII art
- **Visual Feedback**: Particle explosions on collision, web shooting effects

## 🛠️ Development

### Project Structure

```
spidy/
├── spiderman_swing.py    # Main game code
├── setup.py              # Package configuration
├── spidy.rb              # Homebrew formula
├── README.md             # This file
├── LICENSE               # MIT License
└── MANIFEST.in           # Package manifest
```

### Building from Source

```bash
# Create a distributable package
python3 setup.py sdist bdist_wheel

# Install locally
pip install -e .
```

### Creating a Homebrew Formula

The included `spidy.rb` file is a Homebrew formula. To publish:

1. Create a release on GitHub
2. Update the `url` and `sha256` in `spidy.rb`
3. Submit to homebrew-games or create your own tap

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

## 📜 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Credits

Created with ❤️ for terminal game enthusiasts and Spiderman fans everywhere!

## 🐛 Troubleshooting

### Terminal too small
If you see garbled graphics, try maximizing your terminal window or increasing the font size.

### Colors not showing
Make sure your terminal supports 256 colors. Most modern terminals do.

### Game runs too fast/slow
You can adjust `GAME_SPEED` in `spiderman_swing.py` (lower = faster, higher = slower).

### Python curses not available
On some systems, you may need to install ncurses:
```bash
# macOS
brew install ncurses

# Ubuntu/Debian
sudo apt-get install libncurses5-dev
```

## 🎮 Screenshots

```
The game in action (you'll see this in your terminal):

┌─────────────────────────────────────────────────────────┐
│ Score: 342         Speed: 3.2   [SPACE] Swing [Q] Quit  │
│                                                          │
│                         ⚡ <- You (Spiderman)            │
│                      /                                   │
│                    /                                     │
│                  /                                       │
│                /                                         │
│              /                                           │
│            /                                             │
│     ██████                                               │
│     █▓▓▓▓█         ██████                               │
│     █▓▓▓▓█         █▓▓▓▓█     ██████                    │
│     █▓▓▓▓█         █▓▓▓▓█     █▓▓▓▓█                    │
│     █▓▓▓▓█         █▓▓▓▓█     █▼▼▼▼█ <- Obstacle        │
│     ██████         ██████     ██████                     │
└─────────────────────────────────────────────────────────┘
```

---

**Happy Swinging! 🕸️**

May your webs be strong and your reflexes be quick!
