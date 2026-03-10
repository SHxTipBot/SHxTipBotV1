//! SHx Tipping Contract
//!
//! A simple Soroban smart contract that facilitates tips in SHx.
//! It calls `transfer_from` on the SHx Stellar Asset Contract (SAC) to move:
//!   • `amount` SHx from sender → recipient
//!   • `fee`    SHx from sender → treasury
//!
//! **Prerequisites**: The sender must have called `approve` on the SHx SAC
//! granting this contract an allowance ≥ amount + fee.

#![no_std]

use soroban_sdk::{contract, contractimpl, contracttype, Address, Env, token};

/// Persistent storage keys.
#[contracttype]
pub enum DataKey {
    Admin,
    ShxContract,
    Treasury,
}

#[contract]
pub struct TippingContract;

#[contractimpl]
impl TippingContract {
    /// One-time initialisation. Must be called by the deployer before any tips.
    ///
    /// * `admin`        – Admin address (can update config later).
    /// * `shx_contract` – Contract ID of the SHx Stellar Asset Contract (SAC).
    /// * `treasury`     – Address that receives the fee portion of every tip.
    pub fn initialize(env: Env, admin: Address, shx_contract: Address, treasury: Address) {
        // Prevent re-initialisation
        if env.storage().instance().has(&DataKey::Admin) {
            panic!("already initialized");
        }

        admin.require_auth();

        env.storage().instance().set(&DataKey::Admin, &admin);
        env.storage().instance().set(&DataKey::ShxContract, &shx_contract);
        env.storage().instance().set(&DataKey::Treasury, &treasury);
    }

    /// Execute a tip.
    ///
    /// Transfers `amount` SHx from `sender` to `recipient`, and `fee` SHx
    /// from `sender` to the treasury.  Both transfers use the SAC's
    /// `transfer_from`, so the sender must have approved this contract
    /// for at least `amount + fee`.
    ///
    /// * `sender`    – The tipper (must have authorised via SAC `approve`).
    /// * `recipient` – The tip recipient.
    /// * `amount`    – Tip amount in SHx (7-decimal i128, e.g. 50_000_000 = 5 SHx).
    /// * `fee`       – Fee amount in SHx, sent to treasury.
    pub fn tip(env: Env, sender: Address, recipient: Address, amount: i128, fee: i128) {
        assert!(amount > 0, "amount must be > 0");
        assert!(fee >= 0, "fee must be >= 0");

        let shx_contract: Address = env.storage().instance().get(&DataKey::ShxContract).unwrap();
        let treasury: Address = env.storage().instance().get(&DataKey::Treasury).unwrap();

        let shx = token::TokenClient::new(&env, &shx_contract);

        // The contract is the spender; sender must have approved it.
        let contract_address = env.current_contract_address();

        // Transfer tip: sender → recipient
        shx.transfer_from(&contract_address, &sender, &recipient, &amount);

        // Transfer fee: sender → treasury
        if fee > 0 {
            shx.transfer_from(&contract_address, &sender, &treasury, &fee);
        }
    }

    /// Admin-only: update the treasury address.
    pub fn set_treasury(env: Env, new_treasury: Address) {
        let admin: Address = env.storage().instance().get(&DataKey::Admin).unwrap();
        admin.require_auth();
        env.storage().instance().set(&DataKey::Treasury, &new_treasury);
    }

    /// Read the current treasury address.
    pub fn get_treasury(env: Env) -> Address {
        env.storage().instance().get(&DataKey::Treasury).unwrap()
    }
}

// ── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use soroban_sdk::{testutils::Address as _, token::StellarAssetClient, Address, Env};

    fn setup_test() -> (Env, TippingContractClient<'static>, Address, Address, Address, Address) {
        let env = Env::default();
        env.mock_all_auths();

        let contract_id = env.register(TippingContract, ());
        let client = TippingContractClient::new(&env, &contract_id);

        let admin = Address::generate(&env);
        let treasury = Address::generate(&env);
        let sender = Address::generate(&env);
        let recipient = Address::generate(&env);

        // Deploy a test token (simulates the SHx SAC)
        let shx_contract = env.register_stellar_asset_contract_v2(admin.clone());
        let shx_admin = StellarAssetClient::new(&env, &shx_contract.address());

        // Mint tokens to sender
        shx_admin.mint(&sender, &100_000_000_000); // 10,000 SHx

        // Initialize the tipping contract
        client.initialize(&admin, &shx_contract.address(), &treasury);

        // Sender approves the tipping contract
        let shx_token = token::TokenClient::new(&env, &shx_contract.address());
        shx_token.approve(&sender, &contract_id, &100_000_000_000_i128, &6_300_000);

        // Leak env so references are valid
        let env = Box::leak(Box::new(env));
        let client = TippingContractClient::new(env, &contract_id);

        (env.clone(), client, shx_contract.address(), sender, recipient, treasury)
    }

    #[test]
    fn test_tip_with_fee() {
        let (env, client, shx_addr, sender, recipient, treasury) = setup_test();
        let shx = token::TokenClient::new(&env, &shx_addr);

        // Tip 5 SHx with 1 SHx fee
        client.tip(&sender, &recipient, &50_000_000, &10_000_000);

        assert_eq!(shx.balance(&recipient), 50_000_000);   // 5 SHx
        assert_eq!(shx.balance(&treasury), 10_000_000);    // 1 SHx
    }

    #[test]
    fn test_tip_zero_fee() {
        let (env, client, shx_addr, sender, recipient, _treasury) = setup_test();
        let shx = token::TokenClient::new(&env, &shx_addr);

        client.tip(&sender, &recipient, &50_000_000, &0);
        assert_eq!(shx.balance(&recipient), 50_000_000);
    }

    #[test]
    #[should_panic(expected = "amount must be > 0")]
    fn test_tip_zero_amount() {
        let (_env, client, _shx_addr, sender, recipient, _treasury) = setup_test();
        client.tip(&sender, &recipient, &0, &10_000_000);
    }
}
