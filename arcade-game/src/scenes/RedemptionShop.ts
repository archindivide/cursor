import { Scene } from 'phaser';
import { GameManager, SceneKey } from '../systems/GameManager';
import { TicketManager } from '../systems/TicketManager';

interface Prize {
  id: string;
  name: string;
  cost: number;
  description: string;
  color: number;
}

export class RedemptionShop extends Scene {
  private ticketManager: TicketManager;
  private ticketText!: Phaser.GameObjects.Text;
  private prizes: Prize[] = [
    { id: 'toy1', name: 'Small Toy', cost: 10, description: 'A fun little toy', color: 0xff6b6b },
    { id: 'toy2', name: 'Medium Toy', cost: 25, description: 'A cool toy', color: 0x4ecdc4 },
    { id: 'toy3', name: 'Large Toy', cost: 50, description: 'An awesome toy', color: 0xffe66d },
    { id: 'candy1', name: 'Candy Pack', cost: 5, description: 'Sweet treats', color: 0x95e1d3 },
    { id: 'candy2', name: 'Premium Candy', cost: 15, description: 'Delicious candy', color: 0xf38181 },
    { id: 'sticker', name: 'Sticker Pack', cost: 3, description: 'Cool stickers', color: 0xa8e6cf },
    { id: 'keychain', name: 'Keychain', cost: 8, description: 'Stylish keychain', color: 0xffd3a5 },
    { id: 'trophy', name: 'Trophy', cost: 100, description: 'Ultimate prize!', color: 0xffd700 }
  ];
  private purchasedItems: string[] = [];
  private prizeButtons: Phaser.GameObjects.Container[] = [];

  constructor() {
    super({ key: SceneKey.REDEMPTION_SHOP });
    this.ticketManager = TicketManager.getInstance();
    this.loadPurchasedItems();
  }

  create(): void {
    // Background
    this.add.rectangle(640, 360, 1280, 720, 0x1a1a1a);

    // Title
    this.add.text(640, 50, 'Redemption Shop', {
      fontSize: '48px',
      color: '#ffffff',
      fontStyle: 'bold'
    }).setOrigin(0.5);

    // Ticket display
    this.ticketText = this.add.text(640, 120, `Your Tickets: ${this.ticketManager.getTickets()}`, {
      fontSize: '32px',
      color: '#ffff00',
      fontStyle: 'bold'
    }).setOrigin(0.5);

    // Listen for ticket changes
    window.addEventListener('ticketsChanged', this.updateTicketDisplay.bind(this));

    // Create prize grid
    this.createPrizeGrid();

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

    // Inventory section
    this.createInventorySection();
  }

  private createPrizeGrid(): void {
    const startX = 200;
    const startY = 200;
    const spacingX = 280;
    const spacingY = 150;
    const itemsPerRow = 4;

    this.prizes.forEach((prize, index) => {
      const row = Math.floor(index / itemsPerRow);
      const col = index % itemsPerRow;
      const x = startX + col * spacingX;
      const y = startY + row * spacingY;

      this.createPrizeButton(prize, x, y);
    });
  }

  private createPrizeButton(prize: Prize, x: number, y: number): void {
    const container = this.add.container(x, y);
    
    // Background
    const bg = this.add.rectangle(0, 0, 240, 120, prize.color);
    bg.setStrokeStyle(2, 0x000000);
    container.add(bg);

    // Prize name
    const nameText = this.add.text(0, -30, prize.name, {
      fontSize: '18px',
      color: '#000000',
      fontStyle: 'bold'
    }).setOrigin(0.5);
    container.add(nameText);

    // Cost
    const costText = this.add.text(0, 0, `${prize.cost} Tickets`, {
      fontSize: '20px',
      color: '#ffff00',
      fontStyle: 'bold',
      backgroundColor: '#000000',
      padding: { x: 5, y: 2 }
    }).setOrigin(0.5);
    container.add(costText);

    // Description
    const descText = this.add.text(0, 25, prize.description, {
      fontSize: '12px',
      color: '#333333'
    }).setOrigin(0.5);
    container.add(descText);

    // Check if purchased
    if (this.purchasedItems.includes(prize.id)) {
      const purchasedLabel = this.add.text(0, 45, 'PURCHASED', {
        fontSize: '14px',
        color: '#00ff00',
        fontStyle: 'bold',
        backgroundColor: '#000000',
        padding: { x: 5, y: 2 }
      }).setOrigin(0.5);
      container.add(purchasedLabel);
      bg.setAlpha(0.5);
    } else {
      // Make interactive
      bg.setInteractive({ useHandCursor: true });
      bg.on('pointerdown', () => this.purchasePrize(prize));
      bg.on('pointerover', () => bg.setAlpha(0.8));
      bg.on('pointerout', () => bg.setAlpha(1.0));
    }

    this.prizeButtons.push(container);
  }

  private purchasePrize(prize: Prize): void {
    if (this.purchasedItems.includes(prize.id)) {
      return;
    }

    if (this.ticketManager.canAfford(prize.cost)) {
      if (this.ticketManager.removeTickets(prize.cost)) {
        this.purchasedItems.push(prize.id);
        this.savePurchasedItems();
        
        // Show success message
        const message = this.add.text(640, 600, `Purchased ${prize.name}!`, {
          fontSize: '32px',
          color: '#00ff00',
          fontStyle: 'bold',
          backgroundColor: '#000000',
          padding: { x: 20, y: 10 }
        }).setOrigin(0.5);

        this.tweens.add({
          targets: message,
          alpha: 0,
          y: message.y - 50,
          duration: 2000,
          onComplete: () => message.destroy()
        });

        // Refresh display
        this.scene.restart();
      }
    } else {
      // Show error message
      const message = this.add.text(640, 600, 'Not enough tickets!', {
        fontSize: '32px',
        color: '#ff0000',
        fontStyle: 'bold',
        backgroundColor: '#000000',
        padding: { x: 20, y: 10 }
      }).setOrigin(0.5);

      this.tweens.add({
        targets: message,
        alpha: 0,
        duration: 2000,
        onComplete: () => message.destroy()
      });
    }
  }

  private createInventorySection(): void {
    this.add.text(1000, 200, 'Your Inventory:', {
      fontSize: '24px',
      color: '#ffffff',
      fontStyle: 'bold'
    });

    if (this.purchasedItems.length === 0) {
      this.add.text(1000, 250, 'No items yet.\nPlay games to earn tickets!', {
        fontSize: '18px',
        color: '#888888'
      });
    } else {
      this.purchasedItems.forEach((itemId, index) => {
        const prize = this.prizes.find(p => p.id === itemId);
        if (prize) {
          this.add.text(1000, 250 + index * 30, `• ${prize.name}`, {
            fontSize: '16px',
            color: '#ffffff'
          });
        }
      });
    }
  }

  private updateTicketDisplay(): void {
    this.ticketText.setText(`Your Tickets: ${this.ticketManager.getTickets()}`);
  }

  private loadPurchasedItems(): void {
    const saved = localStorage.getItem('arcade_purchased_items');
    if (saved) {
      this.purchasedItems = JSON.parse(saved);
    }
  }

  private savePurchasedItems(): void {
    localStorage.setItem('arcade_purchased_items', JSON.stringify(this.purchasedItems));
  }

  destroy(): void {
    window.removeEventListener('ticketsChanged', this.updateTicketDisplay.bind(this));
    super.destroy();
  }
}
