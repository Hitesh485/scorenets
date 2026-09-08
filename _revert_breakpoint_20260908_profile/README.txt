REVERT BREAKPOINT: 2026-09-08 pre-guest-profile-scrape
Restore: copy _revert_breakpoint_20260908_profile/index.html -> user/profile/index.html
Also revert guest-profile changes in brand/auth.js if needed (ensureGuestProfileGate).
Do NOT touch other routes.
