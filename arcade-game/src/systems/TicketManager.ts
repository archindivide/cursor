export class TicketManager {
  private static instance: TicketManager;
  private tickets: number = 0;
  private readonly STORAGE_KEY = 'arcade_tickets';

  private constructor() {
    this.loadTickets();
  }

  public static getInstance(): TicketManager {
    if (!TicketManager.instance) {
      TicketManager.instance = new TicketManager();
    }
    return TicketManager.instance;
  }

  private loadTickets(): void {
    const saved = localStorage.getItem(this.STORAGE_KEY);
    if (saved) {
      this.tickets = parseInt(saved, 10) || 0;
    }
  }

  private saveTickets(): void {
    localStorage.setItem(this.STORAGE_KEY, this.tickets.toString());
  }

  public getTickets(): number {
    return this.tickets;
  }

  public addTickets(amount: number): void {
    this.tickets += amount;
    this.saveTickets();
    this.emitEvent('ticketsChanged', this.tickets);
  }

  public removeTickets(amount: number): boolean {
    if (this.tickets >= amount) {
      this.tickets -= amount;
      this.saveTickets();
      this.emitEvent('ticketsChanged', this.tickets);
      return true;
    }
    return false;
  }

  public canAfford(amount: number): boolean {
    return this.tickets >= amount;
  }

  private emitEvent(eventName: string, data: any): void {
    window.dispatchEvent(new CustomEvent(eventName, { detail: data }));
  }
}
