import { Scene } from 'phaser';
import { GameManager, SceneKey } from '../systems/GameManager';
import { TicketManager } from '../systems/TicketManager';

export class CoinPusher extends Scene {
  private coins: Phaser.Physics.Arcade.Sprite[] = [];
  private prizes: Phaser.Physics.Arcade.Sprite[] = [];
  private coinsRemaining: number = 8;
  private ticketsEarned: number = 0;
  private platform!: Phaser.GameObjects.Rectangle;
  private platformBody!: Phaser.Physics.Arcade.StaticGroup;
  private dropZone!: Phaser.GameObjects.Zone;
  private collectionZone!: Phaser.GameObjects.Zone;
  private coinsText!: Phaser.GameObjects.Text;
  private ticketsText!: Phaser.GameObjects.Text;
  private ticketManager: TicketManager;
  private prizeValues: number[] = [1, 1, 2, 2, 3, 3, 5, 5, 10];

  constructor() {
    super({ key: SceneKey.COIN_PUSHER });
    this.ticketManager = TicketManager.getInstance();
  }

  create(): void {
    // Background
    this.add.rectangle(640, 360, 1280, 720, 0x2c3e50);

    // Title
    this.add.text(640, 50, 'Coin Pusher!', {
      fontSize: '48px',
      color: '#ffffff',
      fontStyle: 'bold'
    }).setOrigin(0.5);

    // Create platform
    this.createPlatform();

    // UI
    this.coinsText = this.add.text(100, 100, `Coins: ${this.coinsRemaining}`, {
      fontSize: '32px',
      color: '#ffffff',
      backgroundColor: '#000000',
      padding: { x: 10, y: 5 }
    });

    this.ticketsText = this.add.text(100, 150, `Tickets: ${this.ticketsEarned}`, {
      fontSize: '32px',
      color: '#ffff00',
      backgroundColor: '#000000',
      padding: { x: 10, y: 5 }
    });

    this.add.text(640, 650, 'Click on the platform to drop coins!', {
      fontSize: '24px',
      color: '#ffff00'
    }).setOrigin(0.5);

    // Back button
    const backButton = this.add.text(50, 50, '← Back to Arcade', {
      fontSize: '24px',
      color: '#ffffff',
      backgroundColor: '#000000',
      padding: { x: 10, y: 5 }
    }).setInteractive({ useHandCursor: true });

    backButton.on('pointerdown', () => {
      this.endGame();
    });

    // Initial setup
    this.spawnInitialCoinsAndPrizes();
    this.setupInput();
  }

  private createPlatform(): void {
    // Visual platform
    this.platform = this.add.rectangle(640, 400, 800, 300, 0x8b4513);
    this.platform.setStrokeStyle(4, 0x654321);
    
    // Create texture for physics platform
    if (!this.textures.exists('platformPhysics')) {
      const graphics = this.add.graphics();
      graphics.clear();
      graphics.fillStyle(0x8b4513);
      graphics.fillRect(0, 0, 800, 300);
      graphics.generateTexture('platformPhysics', 800, 300);
      graphics.destroy();
    }
    
    // Physics platform (static body)
    this.platformBody = this.physics.add.staticGroup();
    const platformSprite = this.physics.add.staticSprite(640, 400, 'platformPhysics');
    platformSprite.setVisible(false); // Invisible, just for physics
    const body = platformSprite.body as Phaser.Physics.Arcade.StaticBody;
    body.setSize(800, 300);
    this.platformBody.add(platformSprite);

    // Collection zone at front
    this.collectionZone = this.add.zone(640, 550, 800, 50);
    this.physics.add.existing(this.collectionZone, true);
    
    const collectionGraphics = this.add.graphics();
    collectionGraphics.fillStyle(0x00ff00, 0.3);
    collectionGraphics.fillRect(240, 525, 800, 50);
    collectionGraphics.lineStyle(2, 0x00ff00);
    collectionGraphics.strokeRect(240, 525, 800, 50);
    
    this.add.text(640, 550, 'COLLECTION ZONE', {
      fontSize: '20px',
      color: '#ffffff',
      fontStyle: 'bold'
    }).setOrigin(0.5);

    // Drop zone indicator
    this.add.text(640, 200, 'Drop coins here', {
      fontSize: '24px',
      color: '#ffff00'
    }).setOrigin(0.5);
  }

  private spawnInitialCoinsAndPrizes(): void {
    // Spawn some coins on the platform
    for (let i = 0; i < 15; i++) {
      const x = 300 + Math.random() * 680;
      const y = 300 + Math.random() * 150;
      this.createCoin(x, y, false);
    }

    // Spawn prizes
    for (let i = 0; i < 8; i++) {
      const x = 300 + Math.random() * 680;
      const y = 300 + Math.random() * 150;
      this.createPrize(x, y);
    }
  }

  private createCoin(x: number, y: number, isDropped: boolean = true): Phaser.Physics.Arcade.Sprite {
    // Create coin texture if it doesn't exist
    if (!this.textures.exists('coin')) {
      const coinGraphics = this.add.graphics();
      coinGraphics.clear();
      
      // Draw circle centered in texture
      const centerX = 12;
      const centerY = 12;
      
      coinGraphics.fillStyle(0xffd700);
      coinGraphics.fillCircle(centerX, centerY, 12);
      coinGraphics.lineStyle(2, 0x000000);
      coinGraphics.strokeCircle(centerX, centerY, 12);
      coinGraphics.generateTexture('coin', 24, 24);
      coinGraphics.destroy();
    }

    const coin = this.physics.add.sprite(x, y, 'coin');
    coin.setCollideWorldBounds(true);
    coin.setBounce(0.2);
    coin.setFriction(0.8);
    coin.setData('collected', false);

    if (isDropped) {
      coin.setVelocityY(100 + Math.random() * 50);
    }

    // Collision with platform, other coins and prizes
    // Use the existing platformBody created in createPlatform()
    this.physics.add.collider(coin, this.platformBody);
    this.physics.add.collider(coin, this.coins);
    this.physics.add.collider(coin, this.prizes);

    // Check collection zone
    this.physics.add.overlap(coin, this.collectionZone, () => {
      if (!coin.getData('collected')) {
        coin.setData('collected', true);
        this.collectCoin();
        coin.destroy();
      }
    });

    this.coins.push(coin);
    return coin;
  }

  private createPrize(x: number, y: number): Phaser.Physics.Arcade.Sprite {
    const prizeValue = this.prizeValues[Math.floor(Math.random() * this.prizeValues.length)];
    
    // Create prize texture if it doesn't exist
    if (!this.textures.exists(`prize_${prizeValue}`)) {
      const prizeGraphics = this.add.graphics();
      prizeGraphics.clear();
      
      // Draw rectangle centered in texture
      prizeGraphics.fillStyle(0xff6b6b);
      prizeGraphics.fillRect(0, 0, 30, 30);
      prizeGraphics.lineStyle(2, 0x000000);
      prizeGraphics.strokeRect(0, 0, 30, 30);
      prizeGraphics.generateTexture(`prize_${prizeValue}`, 30, 30);
      prizeGraphics.destroy();
    }

    const prize = this.physics.add.sprite(x, y, `prize_${prizeValue}`);
    prize.setCollideWorldBounds(true);
    prize.setBounce(0.1);
    prize.setFriction(0.9);
    prize.setData('value', prizeValue);
    prize.setData('collected', false);

    // Collision with platform, coins and other prizes
    this.physics.add.collider(prize, this.platformBody);
    this.physics.add.collider(prize, this.coins);
    this.physics.add.collider(prize, this.prizes);

    // Check collection zone
    this.physics.add.overlap(prize, this.collectionZone, () => {
      if (!prize.getData('collected')) {
        prize.setData('collected', true);
        this.collectPrize(prizeValue);
        prize.destroy();
      }
    });

    this.prizes.push(prize);
    return prize;
  }

  private setupInput(): void {
    this.input.on('pointerdown', (pointer: Phaser.Input.Pointer) => {
      if (this.coinsRemaining > 0 && pointer.y < 350) {
        this.dropCoin(pointer.x);
      }
    });
  }

  private dropCoin(x: number): void {
    if (this.coinsRemaining <= 0) return;

    // Clamp x to platform bounds
    x = Phaser.Math.Clamp(x, 250, 1030);
    
    this.createCoin(x, 150, true);
    this.coinsRemaining--;
    this.coinsText.setText(`Coins: ${this.coinsRemaining}`);

    // Check if game should end
    if (this.coinsRemaining <= 0) {
      this.time.delayedCall(5000, () => {
        this.endGame();
      });
    }
  }

  private collectCoin(): void {
    // Coins don't give tickets, but they push prizes
  }

  private collectPrize(value: number): void {
    this.ticketsEarned += value;
    this.ticketsText.setText(`Tickets: ${this.ticketsEarned}`);

    // Show popup
    const popup = this.add.text(640, 550, `+${value} Tickets!`, {
      fontSize: '36px',
      color: '#00ff00',
      fontStyle: 'bold',
      backgroundColor: '#000000',
      padding: { x: 10, y: 5 }
    }).setOrigin(0.5);

    this.tweens.add({
      targets: popup,
      y: popup.y - 50,
      alpha: 0,
      duration: 1500,
      onComplete: () => popup.destroy()
    });
  }

  private endGame(): void {
    // Add earned tickets
    if (this.ticketsEarned > 0) {
      this.ticketManager.addTickets(this.ticketsEarned);
    }

    // Show results
    this.add.rectangle(640, 360, 600, 400, 0x000000, 0.9);
    this.add.text(640, 250, 'Game Over!', {
      fontSize: '48px',
      color: '#ffffff',
      fontStyle: 'bold'
    }).setOrigin(0.5);

    this.add.text(640, 320, `Tickets Earned: ${this.ticketsEarned}`, {
      fontSize: '32px',
      color: '#00ff00'
    }).setOrigin(0.5);

    const continueButton = this.add.text(640, 480, 'Return to Arcade', {
      fontSize: '24px',
      color: '#ffffff',
      backgroundColor: '#4a90e2',
      padding: { x: 20, y: 10 }
    }).setOrigin(0.5).setInteractive({ useHandCursor: true });

    continueButton.on('pointerdown', () => {
      this.scene.start(SceneKey.ARCADE_HUB);
    });
  }
}
