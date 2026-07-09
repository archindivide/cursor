# Arcade Hub Game

A 2D arcade hub game built with Phaser.js and TypeScript where you can walk around an arcade, play multiple mini-games to earn tickets, and redeem tickets for prizes.

## Features

- **Arcade Hub**: Walk around a virtual arcade using WASD or arrow keys
- **Three Mini-Games**:
  - **Stop the Spinner**: Click to stop a spinning wheel on high-value segments
  - **Skee Ball**: Launch balls up a ramp to score points in different holes
  - **Coin Pusher**: Drop coins to push prizes off the edge and collect tickets
- **Ticket System**: Earn tickets by playing games, stored persistently in localStorage
- **Redemption Shop**: Spend your tickets on various prizes
- **Persistent Progress**: Your tickets and purchased items are saved between sessions

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser to `http://localhost:3000`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Controls

- **Movement**: WASD or Arrow Keys
- **Interact**: E key (when near arcade machines or shop)
- **Mini-Games**: Mouse clicks and drags (varies by game)

## Game Mechanics

### Stop the Spinner
- Click to stop the spinning wheel
- 5 rounds per game
- Segments worth 10, 25, 50, 100, or 500 points
- Tickets: 1 per 100 points + bonuses

### Skee Ball
- Click and drag to aim, release to launch
- 9 balls per game
- Holes worth 10, 20, 30, 40, 50, or 100 points
- Tickets: 1 per 50 points + bonuses

### Coin Pusher
- Click on the platform to drop coins
- 8 coins per game
- Push prizes off the edge to collect tickets
- Prize values: 1-10 tickets each

## Project Structure

```
arcade-game/
├── src/
│   ├── scenes/          # Game scenes (hub, mini-games, shop)
│   ├── entities/         # Game entities (player, machines)
│   ├── systems/          # Core systems (tickets, game manager)
│   ├── config/           # Game configuration
│   └── main.ts          # Entry point
├── assets/               # Game assets (currently programmatically generated)
└── index.html           # HTML entry point
```

## Technologies

- **Phaser 3**: Game framework
- **TypeScript**: Programming language
- **Vite**: Build tool and dev server

## Future Enhancements

- More mini-games
- High score tracking
- Player progression/leveling
- Enhanced pixel art graphics
- Sound effects and music
- Multiplayer support
