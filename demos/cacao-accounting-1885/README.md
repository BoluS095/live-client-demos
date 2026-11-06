# Cacao Accounting #1885 — Petty-cash status labels

An independent sample patch for the English petty-cash lists, where stored Spanish status codes were appearing as raw values. The change supplies translated display labels for the reconciliation and reimbursement lists while leaving the persisted status values and workflow checks unchanged.

- **Source project:** [cacao-accounting/cacao-accounting](https://github.com/cacao-accounting/cacao-accounting)
- **Source issue:** [#1885 — Petty-cash statuses show raw codes in English UI](https://github.com/cacao-accounting/cacao-accounting/issues/1885)
- **Attribution:** Independently prepared by [BoluS095](https://github.com/BoluS095), based on the public issue above. Unofficial; not affiliated with or endorsed by the maintainers.
- **Patch:** [fix.patch](fix.patch)
- **Validation:** The English gettext catalog was compiled, and a Jinja runtime smoke test rendered all six translated states in each affected template without raw status labels. The full pytest suite was not run in the preparation environment.
- **Indicative amount:** $9, subject to the maintainer's choice. This is not a secured bounty or a promise of acceptance or payment. [Optional direct-payment link](https://buy.stripe.com/28EcN55aC6Wua3HawRb7y0f)

This patch is a demonstration sample prepared from a public issue. It has **not** been submitted upstream. There is no guarantee that it will be reviewed, accepted, merged, or paid. Please check the source issue for current status and contribution guidance before relying on it.
