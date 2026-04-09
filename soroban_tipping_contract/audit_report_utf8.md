[0m[1m[38;5;11mwarning[0m[0m[1m[38;5;15m: [ENHANCEMENT] Use the latest version of Soroban[0m
[0m  [0m[0m[1m[38;5;14m|[0m
[0m  [0m[0m[1m[38;5;14m= [0m[0m[1m[38;5;15mhelp[0m[0m: The latest Soroban version is "25.3.0", and your version is "21.7.1"[0m
[0m  [0m[0m[1m[38;5;14m= [0m[0m[1m[38;5;15mnote[0m[0m: `#[warn(soroban_version)]` on by default[0m

[0m[1m[38;5;11mwarning[0m[0m[1m[38;5;15m: [CRITICAL] This argument comes from a user-supplied argument[0m
[0m  [0m[0m[1m[38;5;14m--> [0m[0msrc\lib.rs:85:51[0m
[0m   [0m[0m[1m[38;5;14m|[0m
[0m[1m[38;5;14m85[0m[0m [0m[0m[1m[38;5;14m|[0m[0m [0m[0m            shx.transfer_from(&contract_address, &sender, &treasury, &fee);[0m
[0m   [0m[0m[1m[38;5;14m|[0m[0m                                                   [0m[0m[1m[38;5;11m^^^^^^[0m
[0m   [0m[0m[1m[38;5;14m|[0m
[0m   [0m[0m[1m[38;5;14m= [0m[0m[1m[38;5;15mnote[0m[0m: `#[warn(unrestricted_transfer_from)]` on by default[0m

[0m[1m[38;5;11mwarning[0m[0m[1m[38;5;15m: [MEDIUM] Unsafe usage of `unwrap`[0m
[0m   [0m[0m[1m[38;5;14m--> [0m[0msrc\lib.rs:174:9[0m
[0m    [0m[0m[1m[38;5;14m|[0m
[0m[1m[38;5;14m174[0m[0m [0m[0m[1m[38;5;14m|[0m[0m [0m[0m        env.storage().instance().get(&DataKey::Treasury).unwrap()[0m
[0m    [0m[0m[1m[38;5;14m|[0m[0m         [0m[0m[1m[38;5;11m^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[0m
[0m    [0m[0m[1m[38;5;14m|[0m
[0m    [0m[0m[1m[38;5;14m= [0m[0m[1m[38;5;15mhelp[0m[0m: Consider pattern matching or using `if let` instead of `unwrap`[0m
[0m    [0m[0m[1m[38;5;14m= [0m[0m[1m[38;5;15mnote[0m[0m: `#[warn(unsafe_unwrap)]` on by default[0m

[0m[1m[38;5;11mwarning[0m[0m[1m[38;5;15m: [ENHANCEMENT] Consider emiting an event when storage is modified[0m
[0m  [0m[0m[1m[38;5;14m--> [0m[0msrc\lib.rs:62:5[0m
[0m   [0m[0m[1m[38;5;14m|[0m
[0m[1m[38;5;14m62[0m[0m [0m[0m[1m[38;5;14m|[0m[0m [0m[0m    pub fn set_admin_pubkey(env: Env, pubkey: soroban_sdk::BytesN<32>) -> Result<(), ContractError> {[0m
[0m   [0m[0m[1m[38;5;14m|[0m[0m     [0m[0m[1m[38;5;11m^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[0m
[0m   [0m[0m[1m[38;5;14m|[0m
[0m   [0m[0m[1m[38;5;14m= [0m[0m[1m[38;5;15mhelp[0m[0m: [0m
[0m   [0m[0m[1m[38;5;14m= [0m[0m[1m[38;5;15mnote[0m[0m: `#[warn(storage_change_events)]` on by default[0m

[0m[1m[38;5;11mwarning[0m[0m[1m[38;5;15m: [ENHANCEMENT] Consider emiting an event when storage is modified[0m
[0m  [0m[0m[1m[38;5;14m--> [0m[0msrc\lib.rs:44:5[0m
[0m   [0m[0m[1m[38;5;14m|[0m
[0m[1m[38;5;14m44[0m[0m [0m[0m[1m[38;5;14m|[0m[0m [0m[0m    pub fn initialize(env: Env, admin: Address, shx_contract: Address, treasury: Address) -> Result<(), ContractError> {[0m
[0m   [0m[0m[1m[38;5;14m|[0m[0m     [0m[0m[1m[38;5;11m^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[0m
[0m   [0m[0m[1m[38;5;14m|[0m
[0m   [0m[0m[1m[38;5;14m= [0m[0m[1m[38;5;15mhelp[0m[0m: [0m

[0m[1m[38;5;11mwarning[0m[0m[1m[38;5;15m: [ENHANCEMENT] Consider emiting an event when storage is modified[0m
[0m   [0m[0m[1m[38;5;14m--> [0m[0msrc\lib.rs:154:5[0m
[0m    [0m[0m[1m[38;5;14m|[0m
[0m[1m[38;5;14m154[0m[0m [0m[0m[1m[38;5;14m|[0m[0m [0m[0m    pub fn set_treasury(env: Env, new_treasury: Address) -> Result<(), ContractError> {[0m
[0m    [0m[0m[1m[38;5;14m|[0m[0m     [0m[0m[1m[38;5;11m^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[0m
[0m    [0m[0m[1m[38;5;14m|[0m
[0m    [0m[0m[1m[38;5;14m= [0m[0m[1m[38;5;15mhelp[0m[0m: [0m

Summary:
+----------------------+----------+----------+--------+-------+-------------+
| [32mCrate               [39;49m | [32mStatus  [39;49m | [32mCritical[39;49m | [32mMedium[39;49m | [32mMinor[39;49m | [32mEnhancement[39;49m | 
+----------------------+----------+----------+--------+-------+-------------+
| [mshx_tipping_contract[39;49m | [mAnalyzed[39;49m | [m1       [39;49m | [m1     [39;49m | [m0    [39;49m | [m4          [39;49m | 
+----------------------+----------+----------+--------+-------+-------------+
[32mreport.md successfully generated.[39;49m

