package org.masdojo.vaultbank

import java.io.File
import java.net.InetSocketAddress
import java.net.Socket

/**
 * Client-side anti-instrumentation / anti-Frida check (RASP technique).
 *
 * VULNERABILITY (MASVS-RESILIENCE-2/3, task 091): the app tries to detect a
 * dynamic-instrumentation toolkit (Frida) attached to its own process and bail
 * out before a hook can reach the gated feature. It looks for the canonical
 * Frida tells — the agent's mappings in `/proc/self/maps`, the default
 * frida-server control port, and a dropped `frida-server` binary. But the whole
 * verdict is one in-process boolean: an attacker who instruments the process
 * simply hooks `isInstrumented()` to return false, so the "app kills itself
 * before you can hook it" defence never fires. The training emulator runs
 * frida-server by design, so this returns true (denied) until the learner's
 * hook flips it.
 */
object AntiTamper {

    private val FRIDA_MAP_MARKERS = arrayOf("frida", "gum-js-loop", "gmain", "frida-agent", "gadget")

    private val FRIDA_SERVER_PATHS = arrayOf(
        "/data/local/tmp/frida-server",
        "/data/local/tmp/re.frida.server",
        "/sbin/frida-server",
    )

    // Frida's default control port; a listener here is a strong instrumentation tell.
    private const val FRIDA_DEFAULT_PORT = 27042

    /** True if the process looks instrumented (Frida attached / present). */
    fun isInstrumented(): Boolean =
        hasFridaInMaps() || hasFridaServerBinary() || fridaPortOpen()

    private fun hasFridaInMaps(): Boolean = try {
        File("/proc/self/maps").readLines().any { line ->
            FRIDA_MAP_MARKERS.any { line.contains(it) }
        }
    } catch (_: Exception) {
        false
    }

    private fun hasFridaServerBinary(): Boolean = FRIDA_SERVER_PATHS.any { File(it).exists() }

    private fun fridaPortOpen(): Boolean = try {
        Socket().use { s ->
            s.connect(InetSocketAddress("127.0.0.1", FRIDA_DEFAULT_PORT), 120)
            true
        }
    } catch (_: Exception) {
        false
    }
}
