# A2A Hub #50 — Honor the rate-limit disable flag

An independent sample patch for `rate-limit.enabled=false` being ignored by the request filter. The patch adds a null-safe bypass when the feature is disabled and a regression test that exercises requests beyond the configured limit.

- **Source project:** [oscarbol09/a2a-hub](https://github.com/oscarbol09/a2a-hub)
- **Source issue:** [#50 — `rate-limit.enabled=false` is ignored](https://github.com/oscarbol09/a2a-hub/issues/50)
- **Attribution:** Independently prepared by [BoluS095](https://github.com/BoluS095), based on the public issue above. Unofficial; not affiliated with or endorsed by the maintainers.
- **Patch:** [fix.patch](fix.patch)
- **Validation:** The prepared `RateLimitFilterTest` suite passed **11/11**, including the regression test for the disabled configuration. This is a local result, not an upstream CI result.
- **Indicative amount:** $25, subject to the maintainer's choice. This is not a secured bounty or a promise of acceptance or payment. [Optional direct-payment link](https://buy.stripe.com/dRm3cv9qSeoWdfTgVfb7y0g)

This patch is a demonstration sample prepared from a public issue. It has **not** been submitted upstream. There is no guarantee that it will be reviewed, accepted, merged, or paid. Please check the source issue for current status and contribution guidance before relying on it.
