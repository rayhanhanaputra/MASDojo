// Native self-ptrace anti-debug guard (RASP technique, task 094).
//
// VULNERABILITY / TRAINING INTENT (MASVS-RESILIENCE-4): on load, the app forks a
// child that ptrace-SEIZEs the parent, so the parent's `TracerPid` in
// /proc/self/status becomes non-zero — the app is "already being traced by
// itself", a classic ptrace-based anti-debug that both (a) makes a naive
// TracerPid check believe a debugger is attached and (b) occupies the single
// ptrace slot to hinder a real debugger. It is still defeatable: the Java gate
// funnels the decision through DebugDetector.isBeingTraced(), so a Frida hook
// that forces it to return false bypasses the guard. This makes the anti-debug
// gate actually engage on a bare device (TracerPid != 0), instead of reading 0
// and unlocking for free.
#include <jni.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <sys/ptrace.h>
#include <sys/types.h>
#include <android/log.h>
#include <linux/ptrace.h>

#ifndef PTRACE_SEIZE
#define PTRACE_SEIZE 0x4206
#endif
#ifndef PR_SET_PTRACER
#define PR_SET_PTRACER 0x59616d61
#endif
#ifndef PR_SET_PTRACER_ANY
#define PR_SET_PTRACER_ANY ((unsigned long)-1)
#endif

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "VaultBank", __VA_ARGS__)

JNIEXPORT jint JNI_OnLoad(JavaVM *vm, void *reserved) {
    (void) vm;
    (void) reserved;

    pid_t parent = getpid();

    // Allow any process (our forthcoming child) to ptrace us, so the SEIZE
    // succeeds even under a restrictive Yama ptrace_scope.
    prctl(PR_SET_PTRACER, PR_SET_PTRACER_ANY, 0, 0, 0);

    int sync_pipe[2];
    if (pipe(sync_pipe) != 0) {
        return JNI_VERSION_1_6;
    }

    pid_t child = fork();
    if (child == 0) {
        // Child: attach to the parent without stopping it, then park forever so
        // we remain the tracer (keeping TracerPid non-zero for the parent).
        close(sync_pipe[0]);
        long r = ptrace(PTRACE_SEIZE, parent, 0, 0);
        char ok = (r == 0) ? 1 : 0;
        (void) write(sync_pipe[1], &ok, 1);
        for (;;) pause();
        _exit(0);
    }

    // Parent: block until the child confirms it attached, so TracerPid is set
    // before JNI_OnLoad returns and the first isBeingTraced() check runs.
    close(sync_pipe[1]);
    char ok = 0;
    (void) read(sync_pipe[0], &ok, 1);
    close(sync_pipe[0]);
    LOGI("guard: self-ptrace %s", ok ? "engaged" : "unavailable");
    return JNI_VERSION_1_6;
}
