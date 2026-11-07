# v1.8.8 release verification — 2026-11-08

- A clean isolated Inno installation and in-place update used a separate product ID, app data, and mutex. Setup closed at 05:08:19.749 and the restart helper logged a visible window at 05:08:20.957: about 1.21 seconds.
- Three isolated normal helper launches took 1.00, 0.82 and 0.80 seconds. Simulating a missed first window detection produced a successful retry in 2.25 seconds. These are local samples, not guarantees for slower systems.
- Name-filtered process discovery retains exact executable path and Windows session checks. If the second launch takes longer, the helper leaves its processes running instead of terminating them at the deadline.
- Initial hidden-window root cause remains unverified; simulated first-start failures that immediately failed on the second start were also observed. The 3-second target is not guaranteed in these cases or on slower systems.
- Installed user files were not upgraded. Actual end-user update and power interruption remain unverified.
