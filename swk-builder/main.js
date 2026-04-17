// main.js — Entry point for the SWK UMD bundle
// Imports the Stellar Wallets Kit and re-exports everything as a single global

// 1. Main SDK class
import { StellarWalletsKit } from '@creit-tech/stellar-wallets-kit/sdk';

// 2. Types, themes, and event system from the root package
import { 
  KitEventType, 
  SwkAppDarkTheme,
  SwkAppLightTheme
} from '@creit-tech/stellar-wallets-kit';

import { FreighterModule } from '@creit-tech/stellar-wallets-kit/modules/freighter';
import { LobstrModule } from '@creit-tech/stellar-wallets-kit/modules/lobstr';
import { xBullModule } from '@creit-tech/stellar-wallets-kit/modules/xbull';

// 3. Default wallet modules (Freighter, Albedo, xBull, LOBSTR/WalletConnect, Hana, etc.)
import { 
  defaultModules 
} from '@creit-tech/stellar-wallets-kit/modules/utils';

// Import WalletConnect specific module to expose it for manual configuration
import { WalletConnectModule } from '@creit-tech/stellar-wallets-kit/modules/wallet-connect';

// 4. Export them all for the UMD bundle (becomes window.StellarKit)
export {
  StellarWalletsKit,
  KitEventType,
  SwkAppDarkTheme,
  SwkAppLightTheme,
  FreighterModule,
  LobstrModule,
  xBullModule,
  defaultModules,
  WalletConnectModule
};
