import { Physics, GameObjects } from 'phaser';

export class Player extends Physics.Arcade.Sprite {
  private speed: number = 200;
  private cursors?: Phaser.Types.Input.Keyboard.CursorKeys;
  private wasdKeys?: {
    W: Phaser.Input.Keyboard.Key;
    A: Phaser.Input.Keyboard.Key;
    S: Phaser.Input.Keyboard.Key;
    D: Phaser.Input.Keyboard.Key;
  };

  constructor(scene: Phaser.Scene, x: number, y: number) {
    // Create texture first if it doesn't exist
    if (!scene.textures.exists('player')) {
      const graphics = scene.add.graphics();
      graphics.fillStyle(0x4a90e2);
      graphics.fillRect(0, 0, 32, 32);
      graphics.generateTexture('player', 32, 32);
      graphics.destroy();
    }
    
    super(scene, x, y, 'player');
    
    scene.add.existing(this);
    scene.physics.add.existing(this);
    
    this.setCollideWorldBounds(true);
    this.setScale(1.5);
    
    // Create animations
    this.createAnimations();
    
    // Set up input
    this.cursors = scene.input.keyboard?.createCursorKeys();
    const keyboard = scene.input.keyboard;
    if (keyboard) {
      this.wasdKeys = {
        W: keyboard.addKey('W'),
        A: keyboard.addKey('A'),
        S: keyboard.addKey('S'),
        D: keyboard.addKey('D')
      };
    }
  }

  private createAnimations(): void {

    // Idle animation (static frame)
    if (!this.scene.anims.exists('playerIdle')) {
      this.scene.anims.create({
        key: 'playerIdle',
        frames: [{ key: 'player', frame: 0 }],
        frameRate: 1,
        repeat: -1
      });
    }

    // Walk animation (same frame for now, can be enhanced later)
    if (!this.scene.anims.exists('playerWalk')) {
      this.scene.anims.create({
        key: 'playerWalk',
        frames: [{ key: 'player', frame: 0 }],
        frameRate: 8,
        repeat: -1
      });
    }

    this.play('playerIdle');
  }

  public update(): void {
    let velocityX = 0;
    let velocityY = 0;

    // Check arrow keys or WASD
    const left = this.cursors?.left.isDown || this.wasdKeys?.A.isDown;
    const right = this.cursors?.right.isDown || this.wasdKeys?.D.isDown;
    const up = this.cursors?.up.isDown || this.wasdKeys?.W.isDown;
    const down = this.cursors?.down.isDown || this.wasdKeys?.S.isDown;

    if (left) {
      velocityX = -this.speed;
    } else if (right) {
      velocityX = this.speed;
    }

    if (up) {
      velocityY = -this.speed;
    } else if (down) {
      velocityY = this.speed;
    }

    this.setVelocity(velocityX, velocityY);

    // Update animation
    if (velocityX !== 0 || velocityY !== 0) {
      if (this.anims.currentAnim?.key !== 'playerWalk') {
        this.play('playerWalk');
      }
    } else {
      if (this.anims.currentAnim?.key !== 'playerIdle') {
        this.play('playerIdle');
      }
    }
  }
}
