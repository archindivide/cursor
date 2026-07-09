import Phaser from 'phaser';
import { gameConfig } from './config/gameConfig';
import { ArcadeHub } from './scenes/ArcadeHub';
import { StopTheSpinner } from './scenes/StopTheSpinner';
import { SkeeBall } from './scenes/SkeeBall';
import { CoinPusher } from './scenes/CoinPusher';
import { RedemptionShop } from './scenes/RedemptionShop';
import { GameOverlay } from './scenes/GameOverlay';
import { GameManager, SceneKey } from './systems/GameManager';

// Register all scenes
gameConfig.scene = [
  ArcadeHub,
  StopTheSpinner,
  SkeeBall,
  CoinPusher,
  RedemptionShop,
  GameOverlay
];

// Create game instance
const game = new Phaser.Game(gameConfig);

// Start main hub scene - overlay will be launched from there
game.scene.start(SceneKey.ARCADE_HUB);

export default game;
