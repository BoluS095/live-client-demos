# Wikipoke #50 — Citation line-number boundary

An independent sample patch for a short citation such as `:2` incorrectly matching a longer line number such as `:20`. The patch makes the lookup reject a digit immediately after the citation and adds a regression test for the false match.

- **Source project:** [webreactiva/wikipoke](https://github.com/webreactiva/wikipoke)
- **Source issue:** [#50 — Citation drift boundary false positive](https://github.com/webreactiva/wikipoke/issues/50)
- **Attribution:** Independently prepared by [BoluS095](https://github.com/BoluS095), based on the public issue above. Unofficial; not affiliated with or endorsed by the maintainers.
- **Patch:** [fix.patch](fix.patch)
- **Validation:** `npm test` passed **66/66** in the prepared project checkout. This is a local result, not an upstream CI result.
- **Indicative amount:** $25, subject to the maintainer's choice. This is not a secured bounty or a promise of acceptance or payment. [Optional direct-payment link](https://buy.stripe.com/dRm3cv9qSeoWdfTgVfb7y0g)

This patch is a demonstration sample prepared from a public issue. It has **not** been submitted upstream. There is no guarantee that it will be reviewed, accepted, merged, or paid. Please check the source issue for current status and contribution guidance before relying on it.
