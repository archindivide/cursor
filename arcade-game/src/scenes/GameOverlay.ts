import { Scene } from 'phaser';
import { TicketManager } from '../systems/TicketManager';

export class GameOverlay extends Scene {
  private ticketText!: Phaser.GameObjects.Text;
  private ticketManager: TicketManager;

  constructor() {
    super({ 
      key: 'GameOverlay',
      active: true,
      visible: true
    });
    this.ticketManager = TicketManager.getInstance();
  }

  create(): void {
    // Create ticket counter in top-right
    // Use game width from config or camera width, with fallback
    const gameWidth = this.cameras.main ? this.cameras.main.width : 1280;
    this.ticketText = this.add.text(
      gameWidth - 20,
      20,
      `Tickets: ${this.ticketManager.getTickets()}`,
      {
        fontSize: '24px',
        color: '#ffffff',
        backgroundColor: '#000000',
        padding: { x: 10, y: 5 }
      }
    );
    this.ticketText.setOrigin(1, 0);
    this.ticketText.setScrollFactor(0);
    this.ticketText.setDepth(1000); // Ensure it's on top

    // Listen for ticket changes
    window.addEventListener('ticketsChanged', this.updateTicketDisplay.bind(this));
  }

  private updateTicketDisplay(): void {
    this.ticketText.setText(`Tickets: ${this.ticketManager.getTickets()}`);
  }

  destroy(): void {
    window.removeEventListener('ticketsChanged', this.updateTicketDisplay.bind(this));
    super.destroy();
  }
}
