import { Scene } from 'phaser';
import { Player } from '../entities/Player';
import { ArcadeMachine } from '../entities/ArcadeMachine';
import { SceneKey } from '../systems/GameManager';

export class ArcadeHub extends Scene {
  private player!: Player;
  private machines: ArcadeMachine[] = [];

  constructor() {
    super({ key: SceneKey.ARCADE_HUB });
  }

  create(): void {
    // Launch overlay scene if not already running (runs in parallel)
    if (!this.scene.isActive('GameOverlay')) {
      this.scene.launch('GameOverlay');
    }

    // Create tilemap background
    this.createBackground();

    // Create player
    this.player = new Player(this, 640, 360);

    // Create arcade machines
    this.createArcadeMachines();

    // Set up camera
    this.cameras.main.setBounds(0, 0, 1920, 1080);
    this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
    this.cameras.main.setZoom(1);

    // Instructions
    this.add.text(20, 20, 'Use WASD or Arrow Keys to move\nPress E near machines to play', {
      fontSize: '18px',
      color: '#ffffff',
      backgroundColor: '#000000',
      padding: { x: 10, y: 5 }
    }).setScrollFactor(0);

    // Shop machine
    const shopZone = this.add.zone(1800, 500, 100, 100);
    this.physics.add.existing(shopZone, true);
    this.physics.add.overlap(this.player, shopZone, () => {
      const interactKey = this.input.keyboard?.addKey('E');
      interactKey?.once('down', () => {
        this.scene.start(SceneKey.REDEMPTION_SHOP);
      });
    });

    this.add.text(1800, 500, 'SHOP\n(Press E)', {
      fontSize: '20px',
      color: '#ffffff',
      backgroundColor: '#8e44ad',
      padding: { x: 10, y: 5 }
    }).setOrigin(0.5);
  }

  private createBackground(): void {
    // Create a simple tile pattern
    const tileSize = 64;
    const graphics = this.add.graphics();
    
    for (let x = 0; x < 1920; x += tileSize) {
      for (let y = 0; y < 1080; y += tileSize) {
        const isDark = (Math.floor(x / tileSize) + Math.floor(y / tileSize)) % 2 === 0;
        graphics.fillStyle(isDark ? 0x34495e : 0x2c3e50);
        graphics.fillRect(x, y, tileSize, tileSize);
      }
    }
    
    // Add walls
    graphics.fillStyle(0x7f8c8d);
    graphics.fillRect(0, 0, 1920, 40); // Top
    graphics.fillRect(0, 1040, 1920, 40); // Bottom
    graphics.fillRect(0, 0, 40, 1080); // Left
    graphics.fillRect(1880, 0, 40, 1080); // Right
  }

  private createArcadeMachines(): void {
    // Stop the Spinner machine
    const spinner = new ArcadeMachine(this, 400, 300, SceneKey.STOP_THE_SPINNER);
    this.add.text(400, 380, 'Stop the Spinner', {
      fontSize: '16px',
      color: '#ffffff',
      backgroundColor: '#000000',
      padding: { x: 5, y: 2 }
    }).setOrigin(0.5);
    this.machines.push(spinner);

    // Skee Ball machine
    const skeeBall = new ArcadeMachine(this, 800, 300, SceneKey.SKEE_BALL);
    this.add.text(800, 380, 'Skee Ball', {
      fontSize: '16px',
      color: '#ffffff',
      backgroundColor: '#000000',
      padding: { x: 5, y: 2 }
    }).setOrigin(0.5);
    this.machines.push(skeeBall);

    // Coin Pusher machine
    const coinPusher = new ArcadeMachine(this, 1200, 300, SceneKey.COIN_PUSHER);
    this.add.text(1200, 380, 'Coin Pusher', {
      fontSize: '16px',
      color: '#ffffff',
      backgroundColor: '#000000',
      padding: { x: 5, y: 2 }
    }).setOrigin(0.5);
    this.machines.push(coinPusher);
  }

  update(): void {
    this.player.update();

    // Check proximity to machines
    this.machines.forEach(machine => {
      machine.checkPlayerProximity(this.player);
    });
  }
}
