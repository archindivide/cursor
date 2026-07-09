import { Scene } from 'phaser';
import { GameManager, SceneKey } from '../systems/GameManager';
import { TicketManager } from '../systems/TicketManager';

export class StopTheSpinner extends Scene {
  private spinner!: Phaser.GameObjects.Container;
  private spinnerAngle: number = 0;
  private spinnerVelocity: number = 0;
  private isSpinning: boolean = false;
  private isStopping: boolean = false;
  private currentRound: number = 0;
  private maxRounds: number = 5;
  private totalScore: number = 0;
  private scoreText!: Phaser.GameObjects.Text;
  private roundText!: Phaser.GameObjects.Text;
  private ticketManager: TicketManager;
  private segments: Array<{ value: number; color: number }> = [
    { value: 10, color: 0xff6b6b },
    { value: 25, color: 0x4ecdc4 },
    { value: 50, color: 0xffe66d },
    { value: 100, color: 0x95e1d3 },
    { value: 500, color: 0xf38181 }
  ];

  constructor() {
    super({ key: SceneKey.STOP_THE_SPINNER });
    this.ticketManager = TicketManager.getInstance();
  }

  create(): void {
    // Background
    this.add.rectangle(640, 360, 1280, 720, 0x2c3e50);

    // Title
    this.add.text(640, 50, 'Stop the Spinner!', {
      fontSize: '48px',
      color: '#ffffff',
      fontStyle: 'bold'
    }).setOrigin(0.5);

    // Create spinner
    this.createSpinner();

    // UI
    this.scoreText = this.add.text(640, 200, `Score: ${this.totalScore}`, {
      fontSize: '32px',
      color: '#ffffff'
    }).setOrigin(0.5);

    this.roundText = this.add.text(640, 250, `Round: ${this.currentRound}/${this.maxRounds}`, {
      fontSize: '24px',
      color: '#ffffff'
    }).setOrigin(0.5);

    this.add.text(640, 650, 'Click to stop the spinner!', {
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
      this.scene.start(SceneKey.ARCADE_HUB);
    });

    // Start first round
    this.startRound();
  }

  private createSpinner(): void {
    const centerX = 640;
    const centerY = 400;
    const radius = 150;

    this.spinner = this.add.container(centerX, centerY);

    // Create segments
    const segmentAngle = (360 / this.segments.length) * (Math.PI / 180);
    
    this.segments.forEach((segment, index) => {
      const startAngle = index * segmentAngle;
      const endAngle = (index + 1) * segmentAngle;

      // Create texture if it doesn't exist
      if (!this.textures.exists(`segment_${index}`)) {
        const graphics = this.add.graphics();
        graphics.clear();
        
        // Draw segment centered in texture
        const centerX = radius;
        const centerY = radius;
        
        graphics.fillStyle(segment.color);
        graphics.lineStyle(2, 0x000000);

        graphics.beginPath();
        graphics.moveTo(centerX, centerY);
        for (let angle = startAngle; angle <= endAngle; angle += 0.1) {
          const x = centerX + Math.cos(angle) * radius;
          const y = centerY + Math.sin(angle) * radius;
          graphics.lineTo(x, y);
        }
        graphics.closePath();
        graphics.fillPath();
        graphics.strokePath();

        graphics.generateTexture(`segment_${index}`, radius * 2, radius * 2);
        graphics.destroy();
      }

      const segmentImage = this.add.image(0, 0, `segment_${index}`);
      segmentImage.setOrigin(0.5);
      this.spinner.add(segmentImage);

      // Add value text
      const textAngle = startAngle + segmentAngle / 2;
      const textX = Math.cos(textAngle) * (radius * 0.7);
      const textY = Math.sin(textAngle) * (radius * 0.7);
      
      const valueText = this.add.text(textX, textY, segment.value.toString(), {
        fontSize: '24px',
        color: '#000000',
        fontStyle: 'bold'
      });
      valueText.setOrigin(0.5);
      this.spinner.add(valueText);
    });

    // Center circle
    const centerCircle = this.add.circle(0, 0, 30, 0xffffff);
    centerCircle.setStrokeStyle(3, 0x000000);
    this.spinner.add(centerCircle);

    // Make spinner clickable
    this.spinner.setInteractive(new Phaser.Geom.Circle(0, 0, radius), Phaser.Geom.Circle.Contains);
    this.spinner.on('pointerdown', () => this.stopSpinner());
  }

  private startRound(): void {
    if (this.currentRound >= this.maxRounds) {
      this.endGame();
      return;
    }

    this.currentRound++;
    this.isSpinning = true;
    this.isStopping = false;
    this.spinnerVelocity = 15 + Math.random() * 5; // Random initial speed
    this.roundText.setText(`Round: ${this.currentRound}/${this.maxRounds}`);
  }

  private stopSpinner(): void {
    if (!this.isSpinning || this.isStopping) return;
    
    this.isStopping = true;
    // Start deceleration
  }

  private getSegmentValue(angle: number): number {
    const normalizedAngle = Phaser.Math.Angle.Normalize(angle);
    const degrees = (normalizedAngle * 180 / Math.PI + 360) % 360;
    const segmentIndex = Math.floor((degrees / (360 / this.segments.length)));
    return this.segments[segmentIndex % this.segments.length].value;
  }

  update(): void {
    if (this.isSpinning) {
      this.spinnerAngle += this.spinnerVelocity * 0.1;
      
      if (this.isStopping) {
        this.spinnerVelocity *= 0.95; // Decelerate
        if (this.spinnerVelocity < 0.1) {
          this.spinnerVelocity = 0;
          this.isSpinning = false;
          this.onSpinnerStopped();
        }
      }
      
      this.spinner.setRotation(this.spinnerAngle);
    }
  }

  private onSpinnerStopped(): void {
    const segmentValue = this.getSegmentValue(this.spinnerAngle);
    this.totalScore += segmentValue;
    this.scoreText.setText(`Score: ${this.totalScore}`);

    // Highlight winning segment
    const normalizedAngle = Phaser.Math.Angle.Normalize(this.spinnerAngle);
    const degrees = (normalizedAngle * 180 / Math.PI + 360) % 360;
    const segmentIndex = Math.floor((degrees / (360 / this.segments.length)));
    
    // Flash effect
    this.tweens.add({
      targets: this.spinner,
      alpha: 0.5,
      duration: 100,
      yoyo: true,
      repeat: 2,
      onComplete: () => {
        // Wait a moment then start next round
        this.time.delayedCall(1000, () => {
          this.startRound();
        });
      }
    });
  }

  private endGame(): void {
    // Calculate tickets (1 ticket per 100 points, bonus for high scores)
    let tickets = Math.floor(this.totalScore / 100);
    if (this.totalScore >= 1000) {
      tickets += 5; // Bonus
    } else if (this.totalScore >= 500) {
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
