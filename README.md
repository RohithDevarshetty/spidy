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

- **Realistic Swinging Physics**: Experience true pendulum-based swinging mechanics
- **Dynamic City Generation**: Procedurally generated buildings create endless gameplay
- **Colorful Terminal Graphics**: Beautiful ASCII art with vibrant colors
- **Obstacle Challenges**: Dodge dangerous obstacles while swinging at high speeds
- **High Score Tracking**: Compete with yourself to beat your best runs
- **Smooth Gameplay**: Optimized for responsive, fluid terminal graphics

## 🎮 Gameplay

You are Spiderman, swinging through a bustling city. Your goal is to travel as far as possible without hitting the ground or crashing into obstacles!

### Controls

- `SPACE` - Shoot web to the nearest building and start swinging
- `Q` - Quit game
- `R` - Restart (when game over)

### Tips

1. **Timing is Everything**: Press SPACE when you're near the peak of your swing to maintain momentum
2. **Look Ahead**: Plan your next swing point while you're still swinging
3. **Avoid Obstacles**: Watch out for the magenta `▼` obstacles on buildings
4. **Keep Moving**: The longer you survive, the higher your score!

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

### Swinging Physics

The game implements realistic pendulum physics:
- Gravity pulls you down constantly
- Web acts as a rope with fixed length
- Momentum is conserved during swings
- Release at the right moment to maximize distance

### Scoring

- Score increases based on distance traveled
- The further you go, the higher your score
- Try to beat your high score with each run!

### Obstacles

- Random obstacles appear on buildings
- Marked with `▼` symbols in magenta
- Colliding with an obstacle ends the game
- Higher buildings = more obstacles

## 🎨 Graphics

Despite being a terminal game, Spidy features:
- Color-coded elements (red Spiderman, blue buildings, yellow webs)
- Smooth animations
- Dynamic camera following
- HUD showing score and speed
- Beautiful ASCII art menus

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
