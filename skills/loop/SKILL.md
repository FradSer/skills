---
name: loop
description: >-
  Run an explicit /loop prompt in the current session on a recurring or
  variable interval, using a host scheduler or a bounded host monitor when
  available.
---

# Loop

Run an explicitly requested `/loop` prompt on a recurring or variable
interval. This skill is a routing and lifecycle contract; it does not assume
that a particular scheduler, background tool, shell, or agent runtime exists.

## Parse

Accept `/loop [interval] <prompt>`.

- Leading interval: `5m /foo`, `30s check status`, `2h run report`.
- Trailing interval: `check deploy every 5m`, `run tests every 10 minutes`.
- No interval: dynamic mode; choose and revise the delay as the work requires.
- Empty prompt: show `Usage: /loop [interval] <prompt>`.

Use intervals such as `30s`, `5m`, `2h`, and `1d`. Normalize unit words to these forms. For a calendar schedule such as “every weekday at 9am”, use the host scheduler's cron support when it has one.

## Choose a scheduling mechanism

Discover the host's scheduling capabilities before creating anything; this
capability check is part of the workflow. Prefer a
durable timer or subscription that can deliver a follow-up prompt to this
session. A background monitor is a valid fallback only when it documents how
it wakes this session, how it is stopped, and how it reports completion. Do
not assume cron, a named monitor tool, or process persistence. If no supported
mechanism exists, report that the host cannot run this loop and stop; do not
start an unbounded local sleeper or watcher; the agent must not start a
background process without a documented cancellation path.

Use a unique stable handle derived from the purpose, such as `loop-check-deploy`. Before creating a schedule, check whether that handle is already active; do not create a duplicate loop.

## Fixed schedule

1. Arm a recurring schedule that sends the literal prompt after each full interval.
2. Run the prompt once immediately after arming it.
3. Ensure the first scheduled wake is only after the first full interval, so startup does not run the prompt twice.
4. Record enough information to stop the schedule later: its handle and, when relevant, its scheduler subscription or process identifier.
5. Confirm the interval, immediate run, first wake time, and the explicit stop
   handle. A recurring schedule may continue until stopped only when the host
   exposes a cancellable subscription.

For a local monitored process, use a bounded, host-owned monitor with one
unique machine-readable sentinel per wake and a documented cancellation path.
Do not create a `while true` process from the agent. If the host cannot bound
and cancel the process, use no local fallback.

Configure the host monitor to wake the agent only for that sentinel. Keep the
loop body quiet and avoid additional work in the background process.

## Dynamic schedule

Use dynamic mode when the next useful check depends on an event or on changing conditions.

1. Run the prompt now.
2. When the host can observe the relevant event (for example, a CI completion, git reference advance, log match, or file change), arm one event watcher.
3. Arm a one-shot time-based fallback wake. Pick a longer fallback while an event watcher is active; otherwise it is the normal cadence.
4. On a wake, read the prompt payload, execute it, then re-arm the next fallback. Re-arm an event watcher only if it exited.
5. Do not start duplicate watchers or sleepers. Every watcher needs a stop
   handle and a finite fallback wake; if either cannot be represented by the
   host, report the limitation instead of starting it.

## Change or stop a loop

To change a schedule, replace the existing one rather than relying on an in-place update: stop or unsubscribe the old handle first, then create the replacement. Some schedulers silently retain a prior configuration when an existing handle is reused.

To stop a loop, locate its active handle, cancel its subscription or terminate
its process using the host's documented mechanism, and consume any final
completion notification so it cannot cause a later wake. Do not arm a
replacement. Confirm that it stopped and why. Never kill an unrelated process
based only on a guessed name or PID.

## Guidance

- Use the title `Loop <schedule>: <prompt>` for background work when the host supports titles.
- Adapt shell syntax to the user's platform.
- On later ticks, report only what changed.
- Prefer the host's monitored background facility over OS cron when the agent needs to receive wake notifications.
