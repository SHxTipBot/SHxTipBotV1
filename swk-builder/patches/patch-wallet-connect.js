/**
 * Postinstall patch for @creit-tech/stellar-wallets-kit WalletConnect module.
 * 
 * Fixes two issues in SWK v2.1.0:
 * 1. Replaces @reown/appkit with @walletconnect/modal to prevent double 
 *    WalletConnect Core initialization (which corrupts the AppKit modal)
 * 2. Adds debug logging for troubleshooting WalletConnect connection flow
 * 
 * Run: node patches/patch-wallet-connect.js
 * Auto-runs via: npm postinstall
 */

const fs = require('fs');
const path = require('path');

const TARGET = path.join(
  __dirname, '..', 'node_modules', '@creit-tech', 'stellar-wallets-kit',
  'sdk', 'modules', 'wallet-connect.module.js'
);

const PATCHED_CONTENT = `import { SignClient } from "@walletconnect/sign-client";
import { WalletConnectModal } from "@walletconnect/modal";
import { ModuleType, Networks } from "../../types/mod.js";
import { disconnect, parseError } from "../utils.js";
import { activeAddress, selectedNetwork, wcSessionPaths } from "../../state/values.js";
export const WALLET_CONNECT_ID = "wallet_connect";
export class WalletConnectModule {
  wcParams;
  moduleType;
  productIcon;
  productId;
  productName;
  productUrl;
  modal;
  signClient;
  initiated;
  constructor(wcParams){
    this.wcParams = wcParams;
    this.moduleType = ModuleType.BRIDGE_WALLET;
    this.productIcon = "https://stellar.creit.tech/wallet-icons/walletconnect.png";
    this.productId = WALLET_CONNECT_ID;
    this.productName = "WalletConnect";
    this.productUrl = "https://walletconnect.com/";
    this.initiated = false;
    if (!wcParams) throw new Error("The WalletConnect modules have required params.");
    // Use @walletconnect/modal (lightweight, doesn't create its own Core)
    this.modal = new WalletConnectModal({
      projectId: wcParams.projectId,
      chains: wcParams.allowedChains || ["stellar:pubnet"],
      walletConnectVersion: 2
    });
    // Wrap the modal to match the open/close API expected by this module
    const originalModal = this.modal;
    this.modal = {
      open: (opts) => originalModal.openModal(opts),
      close: () => originalModal.closeModal()
    };
    // Initialize SignClient (only one Core will be created now)
    SignClient.init({
      projectId: wcParams.projectId,
      metadata: wcParams.metadata,
      ...wcParams.signClientOptions || {}
    }).then((client)=>{
      client.on("display_uri", (uri)=>{
        this.modal.open({ uri });
      });
      client.on("session_delete", (ev)=>{
        this.closeSession(ev.topic);
      });
      this.signClient = client;
      this.initiated = true;
      console.log("[WC Module] SignClient initialized successfully");
    }).catch((err) => {
      console.error("[WC Module] SignClient init failed:", err);
    });
  }
  async isAvailable() {
    return !!this.signClient && !!this.modal;
  }
  async isPlatformWrapper() {
    const options = [
      {
        provider: "freighter",
        platform: "mobile"
      }
    ];
    return !!options.find(({ provider, platform })=>{
      return window.stellar?.provider === provider && window.stellar?.platform === platform;
    });
  }
  async runChecks() {
    if (!await this.isAvailable()) {
      throw parseError(new Error("WalletConnect modules has not been started yet."));
    }
  }
  async getAddress() {
    console.log("[WC Module] getAddress() called");
    await this.runChecks();
    console.log("[WC Module] runChecks passed, selectedNetwork:", selectedNetwork.value);
    if (selectedNetwork.value !== Networks.PUBLIC && selectedNetwork.value !== Networks.TESTNET) {
      throw parseError(new Error(\`Network \${selectedNetwork.value} is not supported by WalletConnect.\`));
    }
    console.log("[WC Module] Calling signClient.connect()...");
    const { uri, approval } = await this.signClient.connect({
      requiredNamespaces: {
        stellar: {
          methods: [
            WalletConnectAllowedMethods.SIGN
          ],
          chains: this.wcParams.allowedChains || [
            WalletConnectTargetChain.PUBLIC
          ],
          events: []
        }
      },
      optionalNamespaces: {
        stellar: {
          methods: [
            WalletConnectAllowedMethods.SIGN_AND_SUBMIT
          ],
          chains: this.wcParams.allowedChains || [
            WalletConnectTargetChain.PUBLIC
          ],
          events: []
        }
      }
    });
    console.log("[WC Module] signClient.connect() returned, uri:", uri ? uri.substring(0, 50) + "..." : "null");
    if (uri) {
      try {
        console.log("[WC Module] Calling modal.open({ uri })...");
        this.modal.open({ uri });
        console.log("[WC Module] modal.open() completed successfully");
      } catch(modalErr) {
        console.error("[WC Module] modal.open() failed:", modalErr);
      }
    }
    try {
      const session = await approval();
      const accounts = session.namespaces.stellar.accounts.map((account)=>account.split(":")[2]);
      wcSessionPaths.value = [
        ...wcSessionPaths.value,
        ...accounts.map((publicKey)=>({
            publicKey,
            topic: session.topic
          }))
      ];
      this.modal.close();
      return {
        address: accounts[0]
      };
    } catch (e) {
      this.modal.close();
      throw e;
    }
  }
  async signTransaction(xdr, opts) {
    await this.runChecks();
    const paths = wcSessionPaths.value;
    const targetSession = paths.find((path)=>{
      return (opts?.address || activeAddress.value) === path.publicKey;
    });
    if (!targetSession) {
      throw parseError(new Error("No WalletConnect session found or it expired for the selected address."));
    }
    const { signedXDR } = await this.signClient.request({
      topic: targetSession.topic,
      chainId: opts?.networkPassphrase === Networks.PUBLIC ? WalletConnectTargetChain.PUBLIC : WalletConnectTargetChain.TESTNET,
      request: {
        method: WalletConnectAllowedMethods.SIGN,
        params: {
          xdr
        }
      }
    });
    return {
      signedTxXdr: signedXDR
    };
  }
  async signAndSubmitTransaction(xdr, opts) {
    await this.runChecks();
    const paths = wcSessionPaths.value;
    const targetSession = paths.find((path)=>{
      return (opts?.address || activeAddress.value) === path.publicKey;
    });
    if (!targetSession) {
      throw parseError(new Error("No WalletConnect session found or it expired for the selected address."));
    }
    const result = await this.signClient.request({
      topic: targetSession.topic,
      chainId: opts?.networkPassphrase === Networks.PUBLIC ? WalletConnectTargetChain.PUBLIC : WalletConnectTargetChain.TESTNET,
      request: {
        method: WalletConnectAllowedMethods.SIGN_AND_SUBMIT,
        params: {
          xdr
        }
      }
    });
    if (result.status !== "success" && result.status !== "pending") {
      throw parseError(new Error(\`Unexpected status from wallet: \${result.status}\`));
    }
    return {
      status: result.status
    };
  }
  async disconnect() {
    if (!this.signClient) {
      throw new Error("WalletConnect is not running yet");
    }
    const sessions = await this.getSessions();
    for (const session of sessions){
      await this.closeSession(session.topic);
    }
  }
  async getSessions() {
    if (!this.signClient) {
      throw new Error("WalletConnect is not running yet");
    }
    return this.signClient.session.values;
  }
  async closeSession(topic, reason) {
    if (!this.signClient) {
      throw new Error("WalletConnect is not running yet");
    }
    wcSessionPaths.value = wcSessionPaths.value.filter((path)=>path.topic !== topic);
    if (wcSessionPaths.value.length === 0) {
      disconnect();
    }
    await this.signClient.disconnect({
      topic,
      reason: {
        message: reason || "Session closed",
        code: -1
      }
    });
  }
  async signAuthEntry() {
    throw {
      code: -3,
      message: 'WalletConnect does not support the "signAuthEntry" function'
    };
  }
  async signMessage() {
    throw {
      code: -3,
      message: 'WalletConnect does not support the "signMessage" function'
    };
  }
  async getNetwork() {
    throw {
      code: -3,
      message: 'WalletConnect does not support the "getNetwork" function'
    };
  }
}
export var WalletConnectTargetChain = /*#__PURE__*/ function(WalletConnectTargetChain) {
  WalletConnectTargetChain["PUBLIC"] = "stellar:pubnet";
  WalletConnectTargetChain["TESTNET"] = "stellar:testnet";
  return WalletConnectTargetChain;
}({});
export var WalletConnectAllowedMethods = /*#__PURE__*/ function(WalletConnectAllowedMethods) {
  WalletConnectAllowedMethods["SIGN"] = "stellar_signXDR";
  WalletConnectAllowedMethods["SIGN_AND_SUBMIT"] = "stellar_signAndSubmitXDR";
  return WalletConnectAllowedMethods;
}({});
`;

if (!fs.existsSync(TARGET)) {
  console.log('[patch] Target file not found, skipping patch:', TARGET);
  process.exit(0);
}

fs.writeFileSync(TARGET, PATCHED_CONTENT, 'utf8');
console.log('[patch] ✅ WalletConnect module patched successfully');
console.log('[patch]    Replaced @reown/appkit with @walletconnect/modal');
console.log('[patch]    Added debug logging to getAddress()');
