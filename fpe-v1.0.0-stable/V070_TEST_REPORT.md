# v0.7 validation

Cross-engine fuzz rerun: PASS, 48 worlds / 48 mutations, 2,808 clusters / 11,232 buds. The retained bridge prints its v0.6 contract version.

Executed locally: Python bridge regression, JavaScript core and embedded-script syntax checks, 2,000 hierarchy operations, and scheduler tests.

Scheduler tests cover two matching 2,000-tick replays, detail/rate comparisons over 2,000 ticks, 2,000 ticks at budget one (all clusters serviced), duplicate/backward/invalid ticks, large time jumps, projection copy isolation, and expansion/collapse invalidation. Source projection remains unchanged.

The hierarchy fuzz selector now uses higher PRNG bits: the prior low-bit branch selection could bias operation coverage.

No real-browser WebGL interaction or performance test was executed. The demo's scheduler integration is syntax-checked; visual QA remains a manual release check. No device performance claims are made.

Historical v0.5/v0.6 reports describe their original releases, not additional v0.7 runs. Bridge and geometry API versions intentionally remain 0.6.0.
