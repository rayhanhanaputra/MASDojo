**Full solution.**

Forge `{"alg":"none"}` header + `{"sub":"alice","role":"admin"}` payload with an empty signature; the server (which accepts alg=none) grants admin and returns `FLAG{jwt_n0n3_f0rg3d}`. Submit it.
