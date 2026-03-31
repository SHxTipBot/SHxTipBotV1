import { defineConfig } from 'vite';
import { nodePolyfills } from 'vite-plugin-node-polyfills';

export default defineConfig({
  plugins: [
    // Polyfill Node.js globals (Buffer, process, crypto, etc.)
    // Required by WalletConnect v2 internals
    nodePolyfills({
      include: ['buffer', 'process', 'crypto', 'stream', 'util', 'events'],
      globals: {
        Buffer: true,
        process: true,
      },
    }),
  ],
  build: {
    // Build as a UMD library for <script> tag usage
    lib: {
      entry: 'main.js',
      name: 'StellarKit',          // Global: window.StellarKit
      fileName: 'wallet-kit-bundle',
      formats: ['umd'],
    },
    rollupOptions: {
      // Stellar SDK is loaded separately via its own <script> tag
      external: ['@stellar/stellar-sdk'],
      output: {
        globals: {
          '@stellar/stellar-sdk': 'StellarSdk',
        },
      },
    },
  },
});
