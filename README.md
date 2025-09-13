Asteroids Game (Python + Pygame)
A clone of the classic Asteroids arcade game, built using Python and the Pygame library.
Control a spaceship, dodge and destroy asteroids, and survive for victory!

Game Overview
In this game, you’ll pilot a spaceship and battle against drifting asteroids in space:
Spaceship Controls:
- ⬅️ Left Arrow – Rotate left
- ➡️ Right Arrow – Rotate right
- ⬆️ Up Arrow – Accelerate forward
- Spacebar – Shoot bullets
- Escape – Quit the game

Gameplay Mechanics:
- Your spaceship continues to move forward when not accelerating, based on its current velocity.
- Large asteroids split into 2 medium ones when shot.
- Medium asteroids split into 2 smaller ones when shot.
- Small asteroids are destroyed when hit.
- If your spaceship collides with an asteroid → Game Over (Defeat)
- Destroy all asteroids → Victory!

Project Structure
Asteroids-game/
│── models/ # Classes for Spaceship, Asteroid, Bullet, etc.
│── utils/ # Helper functions (e.g., sprite loading, random positions)
│── assets/ # Game images & sounds
│── main.py # Game entry point (SpaceRocks class)
│── requirements.txt # Dependencies (pygame)
│── README.md # Project documentation

Installation & Setup 
1. Clone the repository ```bash git clone https://github.com/your-username/Asteroids-game.git cd Asteroids-game
2. Create a virtual environment (optional)
  bash
  python -m venv venv source venv/bin/activate # macOS/Linux venv\Scripts\activate # Windows
3. Install requirements
  bash
  pip install -r requirements.txt
4. Run the game
  bash
  python main.py

Requirements
The game is built with:
pygame==2.0.0

How It Works (Game Loop)
A typical Pygame program runs in a loop that cycles through:
1. Handle Input – Player controls (keyboard, quit events).
2. Process Game Logic – Physics, collisions, asteroid splitting, game state.
3. Draw Game Elements – Rendering the spaceship, asteroids, and bullets.

python
initialize_pygame() 
while True: # Main game loop 
  handle_input() # Player actions 
  process_game_logic() # Collisions & rules 
  draw_game_elements() # Render everything
  
Future Improvements
- Add sound effects & explosion animations
- Score tracking system
- Multiple lives and extra levels
- Improved spaceship acceleration and physics

Credits
- Developed using Python 3 and Pygame.
- Inspired by the classic Asteroids (1979) arcade game.
