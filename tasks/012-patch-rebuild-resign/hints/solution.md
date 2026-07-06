**Full solution.**

Patch `if-eqz v0, :locked` to `if-nez` (or nop it) so execution falls into the premium branch, rebuild with apktool, resign, and run. The unlocked branch returns `FLAG{sm4li_p4tch_unl0ck}`.
