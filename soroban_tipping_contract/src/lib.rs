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

use soroban_sdk::{contract, contracterror, contractimpl, contracttype, symbol_short, token, Address, Env, xdr::ToXdr};

/// Persistent storage keys.
#[contracttype]
pub enum DataKey {
    Admin,
    ShxContract,
    Treasury,
    Version,
}

/// Error codes for the tipping contract.
#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum ContractError {
    AlreadyInitialized = 1,
    NotInitialized = 2,
    InvalidAmount = 3,
    InvalidFee = 4,
    NonceAlreadyUsed = 5,
    AdminPubkeyNotSet = 6,
    InsufficientAllowance = 7,
}

#[contract]
pub struct TippingContract;

#[contractimpl]
impl TippingContract {
    /// One-time initialisation. Must be called by the deployer before any tips.
    pub fn initialize(env: Env, admin: Address, shx_contract: Address, treasury: Address) -> Result<(), ContractError> {
        if env.storage().instance().has(&DataKey::Admin) {
            return Err(ContractError::AlreadyInitialized);
        }

        admin.require_auth();

        env.storage().instance().set(&DataKey::Admin, &admin);
        env.storage()
            .instance()
            .set(&DataKey::ShxContract, &shx_contract);
        env.storage().instance().set(&DataKey::Treasury, &treasury);
        
        // Emit Initialization Event
        env.events().publish(
            (symbol_short!("init"), admin.clone()),
            (shx_contract.clone(), treasury.clone()),
        );
        
        Ok(())
    }

    /// Set the raw Ed25519 public key of the bot (for withdrawal signatures).
    pub fn set_admin_pubkey(env: Env, pubkey: soroban_sdk::BytesN<32>) -> Result<(), ContractError> {
        let admin: Address = env.storage().instance().get(&DataKey::Admin).ok_or(ContractError::NotInitialized)?;
        admin.require_auth();
        env.storage().instance().set(&symbol_short!("adm_pub"), &pubkey);
        
        // Emit Admin Pubkey Set Event
        env.events().publish(
            (symbol_short!("adm_pub"), admin.clone()),
            pubkey,
        );
        
        Ok(())
    }

    /// Execute a tip and emit a TipExecuted event.
    pub fn tip(env: Env, sender: Address, recipient: Address, amount: i128, fee: i128) -> Result<(), ContractError> {
        sender.require_auth();

        if amount <= 0 { return Err(ContractError::InvalidAmount); }
        if fee < 0 { return Err(ContractError::InvalidFee); }

        let shx_contract: Address = env.storage().instance().get(&DataKey::ShxContract).ok_or(ContractError::NotInitialized)?;
        let treasury: Address = env.storage().instance().get(&DataKey::Treasury).ok_or(ContractError::NotInitialized)?;

        let shx = token::TokenClient::new(&env, &shx_contract);


        // 1. Transfer tip: sender → recipient
        shx.transfer(&sender, &recipient, &amount);

        // 2. Transfer fee: sender → treasury
        if fee > 0 {
            shx.transfer(&sender, &treasury, &fee);
        }

        // 3. Emit TipExecuted Event
        env.events().publish(
            (symbol_short!("tip_exec"), sender.clone(), recipient.clone()),
            (amount, fee),
        );
        
        Ok(())
    }

    /// Claim a withdrawal from the House Account into the user's wallet.
    pub fn claim_withdrawal(
        env: Env,
        user: Address,
        amount: i128,
        nonce: u64,
        signature: soroban_sdk::BytesN<64>,
    ) -> Result<(), ContractError> {
        user.require_auth(); // The user pays the gas

        // 1. Replay Protection: Check if this nonce was already used for this user.
        let nonce_key = (symbol_short!("nonce"), user.clone(), nonce);
        if env.storage().persistent().has(&nonce_key) {
            return Err(ContractError::NonceAlreadyUsed);
        }

        // 2. Signature Verification
        let admin_pubkey: soroban_sdk::BytesN<32> = env
            .storage()
            .instance()
            .get(&symbol_short!("adm_pub"))
            .ok_or(ContractError::AdminPubkeyNotSet)?;

        // The message being signed: [ContractAddress, User, Amount, Nonce]
        let mut msg_bin = soroban_sdk::Bytes::new(&env);
        msg_bin.append(&env.current_contract_address().to_xdr(&env));
        msg_bin.append(&user.clone().to_xdr(&env));
        msg_bin.append(&amount.clone().to_xdr(&env));
        msg_bin.append(&nonce.clone().to_xdr(&env));

        env.crypto().ed25519_verify(&admin_pubkey, &msg_bin, &signature);

        // 3. Move SHx from House Account to User
        let house_account: Address = env.storage().instance().get(&DataKey::Admin).ok_or(ContractError::NotInitialized)?;
        let shx_contract: Address = env.storage().instance().get(&DataKey::ShxContract).ok_or(ContractError::NotInitialized)?;
        let shx = token::TokenClient::new(&env, &shx_contract);

        shx.transfer_from(
            &env.current_contract_address(),
            &house_account,
            &user,
            &amount,
        );

        // 4. Record the nonce to prevent double-claiming
        env.storage().persistent().set(&nonce_key, &true);

        // 5. Emit event
        env.events().publish(
            (symbol_short!("withdraw"), user.clone()),
            (amount, nonce),
        );
        
        Ok(())
    }

    /// Admin-only: update the treasury address.
    pub fn set_treasury(env: Env, new_treasury: Address) -> Result<(), ContractError> {
        let admin: Address = env.storage().instance().get(&DataKey::Admin).ok_or(ContractError::NotInitialized)?;
        admin.require_auth();
        env.storage()
            .instance()
            .set(&DataKey::Treasury, &new_treasury);
            
        // Emit Treasury Set Event
        env.events().publish(
            (symbol_short!("treas"), admin.clone()),
            new_treasury,
        );
        
        Ok(())
    }
    
    /// Admin-only: upgrade the contract WASM code.
    pub fn upgrade(env: Env, new_wasm_hash: soroban_sdk::BytesN<32>) -> Result<(), ContractError> {
        let admin: Address = env.storage().instance().get(&DataKey::Admin).ok_or(ContractError::NotInitialized)?;
        admin.require_auth();

        env.deployer().update_current_contract_wasm(new_wasm_hash.clone());
        
        // Emit Upgrade Event
        env.events().publish(
            (symbol_short!("upgrade"), admin.clone()),
            new_wasm_hash,
        );
        
        Ok(())
    }

    /// Read the current treasury address.
    pub fn get_treasury(env: Env) -> Option<Address> {
        env.storage().instance().get(&DataKey::Treasury)
    }

    /// Read the contract version.
    pub fn get_version(env: Env) -> u32 {
        env.storage().instance().get(&DataKey::Version).unwrap_or(0)
    }
}

// ── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use soroban_sdk::{testutils::Address as _, token::StellarAssetClient, Address, Env};

    fn setup_test() -> (Env, Address, Address, Address, Address, Address) {
        let env = Env::default();
        env.mock_all_auths();

        let contract_id = env.register_contract(None, crate::TippingContract);
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

        (
            env,
            contract_id,
            shx_contract.address(),
            sender,
            recipient,
            treasury,
        )
    }

    #[test]
    fn test_tip_with_fee() {
        let (env, contract_id, shx_addr, sender, recipient, treasury) = setup_test();
        let client = TippingContractClient::new(&env, &contract_id);
        let shx = token::TokenClient::new(&env, &shx_addr);

        // Tip 5 SHx with 1 SHx fee
        client.tip(&sender, &recipient, &50_000_000, &10_000_000);

        assert_eq!(shx.balance(&recipient), 50_000_000); // 5 SHx
        assert_eq!(shx.balance(&treasury), 10_000_000); // 1 SHx
    }

    #[test]
    fn test_tip_zero_fee() {
        let (env, contract_id, shx_addr, sender, recipient, _treasury) = setup_test();
        let client = TippingContractClient::new(&env, &contract_id);
        let shx = token::TokenClient::new(&env, &shx_addr);

        client.tip(&sender, &recipient, &50_000_000, &0);
        assert_eq!(shx.balance(&recipient), 50_000_000);
    }

    #[test]
    fn test_tip_zero_amount() {
        let (env, contract_id, _shx_addr, sender, recipient, _treasury) = setup_test();
        let client = TippingContractClient::new(&env, &contract_id);
        let res = client.try_tip(&sender, &recipient, &0, &10_000_000);
        assert_eq!(res, Err(Ok(ContractError::InvalidAmount)));
    }
}
