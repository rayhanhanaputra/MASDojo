.class public Lorg/masdojo/app/IntegrityCheck;

.method public verify()Ljava/lang/String;
    .registers 3
    invoke-static {}, Lorg/masdojo/app/Sig;->matchesOfficial()Z
    move-result v0
    if-eqz v0, :tampered
    const-string v1, "FLAG{1nt3grity_byp4ss3d}"
    return-object v1
    :tampered
    const-string v1, "Tampered"
    return-object v1
.end method
