.class public Lorg/masdojo/app/PremiumGate;

.method public unlock()Ljava/lang/String;
    .registers 3
    invoke-static {}, Lorg/masdojo/app/License;->isPremium()Z
    move-result v0
    if-eqz v0, :locked
    const-string v1, "FLAG{sm4li_p4tch_unl0ck}"
    return-object v1
    :locked
    const-string v1, "Locked"
    return-object v1
.end method
