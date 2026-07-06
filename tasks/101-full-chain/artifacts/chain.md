# Full chain
1. RE the APK, recover the embedded API key (Module 1 technique).
2. Read the encrypted vault from local storage, decrypt with that key (Modules 2-3).
3. Bypass SSL pinning and intercept the vault-sync API (Modules 5-6).
4. IDOR the sync endpoint to read the admin vault (Module 7).
5. The admin vault yields the final flag: FLAG{full_ch41n_pwn3d}
