import { Scene } from 'phaser';

export enum SceneKey {
  ARCADE_HUB = 'ArcadeHub',
  STOP_THE_SPINNER = 'StopTheSpinner',
  SKEE_BALL = 'SkeeBall',
  COIN_PUSHER = 'CoinPusher',
  REDEMPTION_SHOP = 'RedemptionShop',
  GAME_OVERLAY = 'GameOverlay'
}

export class GameManager {
  private static instance: GameManager;
  private currentScene: Scene | null = null;

  private constructor() {}

  public static getInstance(): GameManager {
    if (!GameManager.instance) {
      GameManager.instance = new GameManager();
    }
    return GameManager.instance;
  }

  public setCurrentScene(scene: Scene): void {
    this.currentScene = scene;
  }

  public getCurrentScene(): Scene | null {
    return this.currentScene;
  }

  public transitionToScene(sceneKey: SceneKey, data?: any): void {
    if (this.currentScene) {
      this.currentScene.scene.start(sceneKey, data);
    }
  }

  public getScene(sceneKey: SceneKey): Scene | null {
    if (this.currentScene) {
      return this.currentScene.scene.get(sceneKey);
    }
    return null;
  }
}
