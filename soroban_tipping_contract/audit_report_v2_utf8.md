[0m[1m[38;5;11mwarning[0m[0m[1m[38;5;15m: [ENHANCEMENT] Use the latest version of Soroban[0m
[0m  [0m[0m[1m[38;5;14m|[0m
[0m  [0m[0m[1m[38;5;14m= [0m[0m[1m[38;5;15mhelp[0m[0m: The latest Soroban version is "25.3.0", and your version is "21.7.7"[0m
[0m  [0m[0m[1m[38;5;14m= [0m[0m[1m[38;5;15mnote[0m[0m: `#[warn(soroban_version)]` on by default[0m

[0m[1m[38;5;11mwarning[0m[0m[1m[38;5;15m: [CRITICAL] This argument comes from a user-supplied argument[0m
[0m  [0m[0m[1m[38;5;14m--> [0m[0msrc\lib.rs:99:51[0m
[0m   [0m[0m[1m[38;5;14m|[0m
[0m[1m[38;5;14m99[0m[0m [0m[0m[1m[38;5;14m|[0m[0m [0m[0m            shx.transfer_from(&contract_address, &sender, &treasury, &fee);[0m
[0m   [0m[0m[1m[38;5;14m|[0m[0m                                                   [0m[0m[1m[38;5;11m^^^^^^[0m
[0m   [0m[0m[1m[38;5;14m|[0m
[0m   [0m[0m[1m[38;5;14m= [0m[0m[1m[38;5;15mnote[0m[0m: `#[warn(unrestricted_transfer_from)]` on by default[0m

Summary:
+----------------------+----------+----------+--------+-------+-------------+
| [32mCrate               [39;49m | [32mStatus  [39;49m | [32mCritical[39;49m | [32mMedium[39;49m | [32mMinor[39;49m | [32mEnhancement[39;49m | 
+----------------------+----------+----------+--------+-------+-------------+
| [mshx_tipping_contract[39;49m | [mAnalyzed[39;49m | [m1       [39;49m | [m0     [39;49m | [m0    [39;49m | [m1          [39;49m | 
+----------------------+----------+----------+--------+-------+-------------+
[32mreport.md successfully generated.[39;49m

