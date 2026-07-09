import { Scene } from 'phaser';
import { GameManager, SceneKey } from '../systems/GameManager';
import { TicketManager } from '../systems/TicketManager';

export class SkeeBall extends Scene {
  private balls: Phaser.Physics.Arcade.Sprite[] = [];
  private ballsRemaining: number = 9;
  private totalScore: number = 0;
  private currentBall: Phaser.Physics.Arcade.Sprite | null = null;
  private isAiming: boolean = false;
  private aimStartX: number = 0;
  private aimStartY: number = 0;
  private powerMeter!: Phaser.GameObjects.Graphics;
  private scoreText!: Phaser.GameObjects.Text;
  private ballsText!: Phaser.GameObjects.Text;
  private ticketManager: TicketManager;
  private holes: Array<{ x: number; y: number; radius: number; value: number }> = [];
  private holeSprites!: Phaser.Physics.Arcade.StaticGroup;

  constructor() {
    super({ key: SceneKey.SKEE_BALL });
    this.ticketManager = TicketManager.getInstance();
  }

  create(): void {
    // Initialize physics group
    this.holeSprites = this.physics.add.staticGroup();

    // Background
    this.add.rectangle(640, 360, 1280, 720, 0x2c3e50);

    // Title
    this.add.text(640, 50, 'Skee Ball!', {
      fontSize: '48px',
      color: '#ffffff',
      fontStyle: 'bold'
    }).setOrigin(0.5);

    // Create ramp and holes
    this.createRamp();

    // UI
    this.scoreText = this.add.text(100, 100, `Score: ${this.totalScore}`, {
      fontSize: '32px',
      color: '#ffffff',
      backgroundColor: '#000000',
      padding: { x: 10, y: 5 }
    });

    this.ballsText = this.add.text(100, 150, `Balls: ${this.ballsRemaining}`, {
      fontSize: '32px',
      color: '#ffffff',
      backgroundColor: '#000000',
      padding: { x: 10, y: 5 }
    });

    this.add.text(640, 650, 'Click and drag to aim, release to launch!', {
      fontSize: '24px',
      color: '#ffff00'
    }).setOrigin(0.5);

    // Power meter
    this.powerMeter = this.add.graphics();

    // Back button
    const backButton = this.add.text(50, 50, '← Back to Arcade', {
      fontSize: '24px',
      color: '#ffffff',
      backgroundColor: '#000000',
      padding: { x: 10, y: 5 }
    }).setInteractive({ useHandCursor: true });

    backButton.on('pointerdown', () => {
      this.scene.start(SceneKey.ARCADE_HUB);
    });

    // Input handlers
    this.input.on('pointerdown', this.startAim, this);
    this.input.on('pointermove', this.updateAim, this);
    this.input.on('pointerup', this.launchBall, this);

    // Start first ball
    this.createNewBall();
  }

  private createRamp(): void {
    // Ramp base
    const rampGraphics = this.add.graphics();
    rampGraphics.clear();
    rampGraphics.fillStyle(0x8b4513);
    rampGraphics.fillRect(200, 500, 880, 200);
    rampGraphics.lineStyle(4, 0x654321);
    rampGraphics.strokeRect(200, 500, 880, 200);

    // Ramp surface (angled)
    rampGraphics.fillStyle(0xd2691e);
    rampGraphics.beginPath();
    rampGraphics.moveTo(200, 500);
    rampGraphics.lineTo(1080, 400);
    rampGraphics.lineTo(1080, 500);
    rampGraphics.closePath();
    rampGraphics.fillPath();
    rampGraphics.strokePath();

    // Scoring holes
    this.holes = [
      { x: 300, y: 450, radius: 40, value: 10 },
      { x: 400, y: 420, radius: 40, value: 20 },
      { x: 500, y: 400, radius: 40, value: 30 },
      { x: 600, y: 380, radius: 40, value: 40 },
      { x: 700, y: 360, radius: 50, value: 50 },
      { x: 900, y: 340, radius: 60, value: 100 }
    ];

    this.holes.forEach((hole, index) => {
      // Create hole texture if it doesn't exist
      if (!this.textures.exists(`hole_${index}`)) {
        const holeGraphics = this.add.graphics();
        holeGraphics.clear();
        
        // Draw circle centered in texture
        const centerX = hole.radius;
        const centerY = hole.radius;
        
        holeGraphics.fillStyle(0x1a1a1a);
        holeGraphics.fillCircle(centerX, centerY, hole.radius);
        holeGraphics.lineStyle(2, 0xffffff);
        holeGraphics.strokeCircle(centerX, centerY, hole.radius);
        holeGraphics.generateTexture(`hole_${index}`, hole.radius * 2, hole.radius * 2);
        holeGraphics.destroy();
      }

      const holeSprite = this.add.image(hole.x, hole.y, `hole_${index}`);
      holeSprite.setOrigin(0.5);

      // Value label
      this.add.text(hole.x, hole.y, hole.value.toString(), {
        fontSize: '20px',
        color: '#ffffff',
        fontStyle: 'bold'
      }).setOrigin(0.5);

      // Add to physics group for collision
      const physicsSprite = this.physics.add.staticSprite(hole.x, hole.y, `hole_${index}`);
      physicsSprite.setVisible(false); // Invisible, just for physics
      const body = physicsSprite.body as Phaser.Physics.Arcade.StaticBody;
      body.setCircle(hole.radius);
      this.holeSprites.add(physicsSprite);
    });
  }

  private createNewBall(): void {
    if (this.ballsRemaining <= 0) {
      this.endGame();
      return;
    }

    // Create ball texture if it doesn't exist
    if (!this.textures.exists('skeeBall')) {
      const ballGraphics = this.add.graphics();
      ballGraphics.clear();
      
      // Draw circle centered in texture
      const centerX = 15;
      const centerY = 15;
      
      ballGraphics.fillStyle(0xff0000);
      ballGraphics.fillCircle(centerX, centerY, 15);
      ballGraphics.lineStyle(2, 0x000000);
      ballGraphics.strokeCircle(centerX, centerY, 15);
      ballGraphics.generateTexture('skeeBall', 30, 30);
      ballGraphics.destroy();
    }

    const ball = this.physics.add.sprite(250, 650, 'skeeBall');
    ball.setCollideWorldBounds(true);
    ball.setBounce(0.3);
    ball.setFriction(0.1);
    ball.setData('scored', false);

    this.currentBall = ball;
    this.balls.push(ball);

    // Collision with holes
    this.physics.add.overlap(ball, this.holeSprites, (ballObj: any, holeObj: any) => {
      if (!ball.getData('scored')) {
        const holeIndex = parseInt(holeObj.texture.key.replace('hole_', ''));
        const hole = this.holes[holeIndex];
        if (hole) {
          ball.setData('scored', true);
          this.scoreHole(hole.value);
        }
      }
    });
  }

  private startAim(pointer: Phaser.Input.Pointer): void {
    if (!this.currentBall || this.currentBall.body!.velocity.x !== 0 || this.currentBall.body!.velocity.y !== 0) {
      return;
    }

    this.isAiming = true;
    this.aimStartX = pointer.x;
    this.aimStartY = pointer.y;
  }

  private updateAim(pointer: Phaser.Input.Pointer): void {
    if (!this.isAiming || !this.currentBall) return;

    const dx = pointer.x - this.aimStartX;
    const dy = pointer.y - this.aimStartY;
    const power = Math.min(Math.sqrt(dx * dx + dy * dy), 200);

    // Draw power meter
    this.powerMeter.clear();
    this.powerMeter.fillStyle(0x00ff00);
    this.powerMeter.fillRect(50, 200, power / 2, 20);
    this.powerMeter.lineStyle(2, 0xffffff);
    this.powerMeter.strokeRect(50, 200, 100, 20);
  }

  private launchBall(pointer: Phaser.Input.Pointer): void {
    if (!this.isAiming || !this.currentBall) return;

    this.isAiming = false;
    this.powerMeter.clear();

    const dx = pointer.x - this.aimStartX;
    const dy = pointer.y - this.aimStartY;
    const power = Math.min(Math.sqrt(dx * dx + dy * dy), 200);
    const angle = Math.atan2(dy, dx);

    // Launch ball
    const velocityX = Math.cos(angle) * power * 3;
    const velocityY = Math.sin(angle) * power * 3;
    
    this.currentBall.setVelocity(velocityX, velocityY);

    // Wait for ball to stop or go off screen, then next ball
    this.time.delayedCall(3000, () => {
      if (this.currentBall) {
        this.ballsRemaining--;
        this.ballsText.setText(`Balls: ${this.ballsRemaining}`);
        
        if (this.currentBall.active) {
          this.currentBall.destroy();
        }
        this.currentBall = null;
        
        this.time.delayedCall(500, () => {
          this.createNewBall();
        });
      }
    });
  }

  private scoreHole(value: number): void {
    this.totalScore += value;
    this.scoreText.setText(`Score: ${this.totalScore}`);

    // Show score popup
    const popup = this.add.text(this.currentBall!.x, this.currentBall!.y - 30, `+${value}`, {
      fontSize: '32px',
      color: '#ffff00',
      fontStyle: 'bold'
    });
    
    this.tweens.add({
      targets: popup,
      y: popup.y - 50,
      alpha: 0,
      duration: 1000,
      onComplete: () => popup.destroy()
    });
  }

  private endGame(): void {
    // Calculate tickets (1 ticket per 50 points, bonus for high scores)
    let tickets = Math.floor(this.totalScore / 50);
    if (this.totalScore >= 500) {
      tickets += 5; // Bonus
    } else if (this.totalScore >= 300) {
      tickets += 2; // Small bonus
    }

    this.ticketManager.addTickets(tickets);

    // Show results
    this.add.rectangle(640, 360, 600, 400, 0x000000, 0.9);
    this.add.text(640, 250, 'Game Over!', {
      fontSize: '48px',
      color: '#ffffff',
      fontStyle: 'bold'
    }).setOrigin(0.5);

    this.add.text(640, 320, `Final Score: ${this.totalScore}`, {
      fontSize: '32px',
      color: '#ffff00'
    }).setOrigin(0.5);

    this.add.text(640, 380, `Tickets Earned: ${tickets}`, {
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
