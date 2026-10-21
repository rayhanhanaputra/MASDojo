package org.masdojo.vaultbank

/**
 * Premium-feature entitlement.
 *
 * VULNERABILITY (MASVS-RESILIENCE-1, task 042): the entire "is this user allowed
 * the premium feature?" decision is this one in-process boolean. It always
 * returns false on this build, so the feature stays locked — until an attacker
 * hooks `isUnlocked()` (Frida) and forces it to return true, at which point the
 * gated reward is revealed. A purely client-side entitlement check is worthless
 * because the client is fully under the attacker's control.
 */
object FeatureGate {

    /** The whole premium gate is this single flippable boolean. */
    fun isUnlocked(): Boolean = false
}
