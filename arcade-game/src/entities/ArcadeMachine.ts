import { GameObjects, Physics } from 'phaser';
import { SceneKey } from '../systems/GameManager';

export class ArcadeMachine extends Physics.Arcade.Sprite {
  private machineType: SceneKey;
  private interactionZone: Physics.Arcade.Body;
  private canInteract: boolean = false;
  private interactKey?: Phaser.Input.Keyboard.Key;

  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    machineType: SceneKey
  ) {

    super(scene, x, y, 'arcadeMachine');
    // Create visual representation first
    this.createVisual(scene, machineType);


    this.machineType = machineType;

    scene.add.existing(this);
    scene.physics.add.existing(this);

    this.setImmovable(true);
    this.setScale(2);

    // Set up interaction
    this.interactKey = scene.input.keyboard?.addKey('E');
    this.interactKey?.on('down', () => this.handleInteraction());

    // Create interaction zone (larger than sprite) - use fixed size since we know dimensions
    this.interactionZone = this.body as Physics.Arcade.Body;
    this.interactionZone.setSize(64 * 1.5, 80 * 1.5);
  }

  private createVisual(scene: Phaser.Scene, machineType: SceneKey): void {
    // Only create texture if it doesn't exist
    if (scene.textures.exists('arcadeMachine')) {
      return;
    }

    // Create machine sprite based on type
    const graphics = scene.add.graphics();

    switch (machineType) {
      case SceneKey.STOP_THE_SPINNER:
        graphics.fillStyle(0xff6b6b);
        break;
      case SceneKey.SKEE_BALL:
        graphics.fillStyle(0x4ecdc4);
        break;
      case SceneKey.COIN_PUSHER:
        graphics.fillStyle(0xffe66d);
        break;
      default:
        graphics.fillStyle(0x95a5a6);
    }

    graphics.fillRect(0, 0, 64, 80);
    graphics.lineStyle(2, 0x000000);
    graphics.strokeRect(0, 0, 64, 80);

    // Add screen area
    graphics.fillStyle(0x1a1a1a);
    graphics.fillRect(8, 8, 48, 40);

    graphics.generateTexture('arcadeMachine', 64, 80);
    graphics.destroy();
  }

  public checkPlayerProximity(player: Physics.Arcade.Sprite): void {
    const distance = Phaser.Math.Distance.Between(
      this.x,
      this.y,
      player.x,
      player.y
    );

    this.canInteract = distance < 100;

    // Visual feedback
    if (this.canInteract) {
      this.setTint(0xffffff);
      this.setAlpha(1.0);
    } else {
      this.clearTint();
      this.setAlpha(0.8);
    }
  }

  private handleInteraction(): void {
    if (this.canInteract) {
      this.scene.scene.start(this.machineType);
    }
  }

  public getMachineType(): SceneKey {
    return this.machineType;
  }
}
