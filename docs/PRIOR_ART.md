# SkyGuard AI — Prior Art & Validation Positioning

**Problem Statement 26073 — AI/ML-Based Intelligent Anomaly Detection for Automatic Weather Stations**

This document answers the two questions a reviewer will (rightly) push on:

1. **"How do we know this isn't already solved?"** — i.e. what is the prior art, and what is
   actually novel here versus reusing known techniques.
2. **"Which previous solution did you validate against?"** — i.e. what is the baseline.

The honest short version is at the top; the evidence tables and the candid gaps follow.

> **A note on intellectual honesty.** SkyGuard does **not** claim to invent anomaly detection,
> spatial consistency checking, isolation forests, or autoencoders. Every one of those is prior art
> and is cited below. The claim is narrower and defensible: **no single fielded system combines
> physics-thermodynamic reasoning + a multi-model ensemble + cross-station corroboration to make an
> explicit *sensor-fault-vs-genuine-weather* decision, name the fault, self-heal the value, and
> explain itself — in real time.** Reviewers respect a precise novelty claim far more than a vague
> "we built something new," so this is framed precisely on purpose.

---

## TL;DR — the two answers

**"How do we know it isn't already solved?"**
Operational weather-data QC is a mature field (WMO standards, NOAA MADIS, MET Norway TITAN, the
Oklahoma Mesonet QA suite). But those systems overwhelmingly *flag or reject* suspect data for
downstream assimilation or climate-record cleaning. They do **not**, in one integrated real-time
package: reason from thermodynamics, fuse four detectors, use neighbours specifically to tell a
*genuine storm* from a *broken sensor*, classify the fault into a named root cause with its own
confidence, repair the value while quarantining the original, and explain each decision. That
*integration and the explicit fault-vs-weather decision* is the unsolved part we target.

**"Which previous solution did you validate against?"**
Candidly: we have **not yet** run a head-to-head against a *named* fielded system on identical data.
What we *have* validated is an **ablation against the standard-method baselines themselves** — each
of Isolation Forest, an autoencoder, EWMA+CUSUM statistics, and a physics rule-checker **alone** —
on real NOAA historical weather with injected faults, and shown the integrated system beats every
single one (real-data **ensemble F1 ≈ 91.5% at 0.97 AUC vs. best single component 78.6% F1**). The
honest, high-value next step — and the strongest possible answer to this exact question — is a
direct head-to-head reproducing a named spatial-QC baseline (MET Norway's **titanlib** SCT/buddy
check) on our same NOAA replay. See [§4](#4-what-we-validated-against--stated-honestly).

---

## 1. Prior art — operational & standardised QC systems

These are the "previous solutions" a domain judge has in mind. All are real, documented, and in
production use.

| Prior solution | What it is / does | Core techniques | Gap vs. SkyGuard (what it does *not* do) |
|---|---|---|---|
| **WMO QC standards** — CIMO Guide (WMO-No. 8), WMO-No. 305, Zahumenský (2004) *Guidelines on QC for AWS data* | The canonical rulebook national met services implement for AWS data | Gross/plausible-range limits, time-consistency (step + persistence), internal consistency (e.g. dew point ≤ temperature), spatial consistency | Static thresholds; rule-based only, no learning; produces a *quality flag* (good/suspect/erroneous), **not** a named root cause; an extreme-but-real value is often flagged "suspect" — i.e. the false-alarm-on-real-weather problem is left to the human; no self-healing; no per-reading explanation |
| **NOAA MADIS** (Meteorological Assimilation Data Ingest System) | National ingest hub that QCs surface obs for assimilation & distribution | 3 levels: (1) validity/range, (2) internal + temporal consistency, (3) spatial/buddy check; emits QC flags (screened / verified / spatially-consistent / rejected …) | Built for *ingest & flagging*, not on-station real-time decisioning; rejects/flags rather than **repairs**; no learned temporal-shape model; no fault taxonomy with confidence; no explainability surface for an operator |
| **MET Norway TITAN / `titanlib`** | Open-source library + system for automatic **spatial** QC, incl. dense/crowdsourced networks (e.g. citizen stations) | Spatial Consistency Test (SCT), buddy check, buddy-event check, isolation check, first-guess/background check, range & climatology checks | Predominantly **spatial + statistical** — its power *requires a dense neighbour network* (the mirror image of our sparse-network limitation); no thermodynamic engine (Magnus-Tetens dew point/VPD), no neural temporal model, no named root-cause class, no self-heal, no per-decision explanation |
| **Oklahoma Mesonet QA** — Shafer et al. (2000), *J. Atmos. Oceanic Technol.* | The reference gold-standard QA suite for a real operational mesonet | Range, step, persistence, spatial, and like-instrument/internal-consistency checks **+ trained human review** and complex QA flags | Rule-based **with a human in the loop** — not a fully autonomous real-time verdict; mesonet-specific tuning; no ML ensemble, no self-healing, no automated fault-vs-weather class with confidence |
| **HadISD** — Dunn et al. (2012, 2016), *Climate of the Past* | Automated QC for the global sub-daily station climate record | Battery of automated tests: climatological outlier, distributional-gap, streak/frequent-value, spike, record checks | **Retrospective / offline** climate-record cleaning, not real-time on-station; rule/statistical; no repair, no root-cause classifier, no learned fault-vs-weather discrimination |

**Pattern across all five:** they are excellent at *flagging suspect data*. None of them, in one
real-time package, *decides fault-vs-weather, names the fault, repairs it, and explains the call.*

---

## 2. Prior art — academic & ML methods (the "baselines")

These are the algorithmic building blocks. SkyGuard **uses several of them as components** — which
is the point: the contribution is the fusion and the domain reasoning around them, not the raw
algorithms.

| Method | What it does | Gap as a *standalone* solution to PS 26073 | Role in SkyGuard |
|---|---|---|---|
| **Isolation Forest** — Liu, Ting & Zhou (2008), *ICDM* | Unsupervised, tree-based multivariate outlier scoring | An outlier is an outlier — it **cannot tell a real storm from a broken sensor**; no physics; no temporal shape; no root cause. (On our real data, alone ≈ **50.3% F1**.) | 1 of 4 detectors (weight 0.20) — the only one seeing T/P/RH *jointly* |
| **Autoencoder / LSTM-AD reconstruction** — Sakurada & Yairi (2014); Malhotra et al. (2015); Hundman et al. (2018, KDD) | Learns "normal" trajectories; high reconstruction error ⇒ anomaly | Needs representative training; flags shape outliers regardless of *cause*; degrades across climatically different stations. (On our real data, alone ≈ **31.3% F1**.) | 1 of 4 detectors (weight 0.15) — catches temporal-shape faults others miss |
| **EWMA / CUSUM statistical filters** (classical SPC) | Streaming detection of level shifts, drift, and stuck sensors | Univariate, no physics, no spatial context; confuses slow drift with slow real weather without help | 1 of 4 detectors (weight 0.20); climatology deseasonalisation added to fix the drift-vs-diurnal confound |
| **Physics-guided / theory-guided ML** — Karpatne et al. (2017); Raissi et al. (2019, PINNs); Willard et al. (survey) | Injects physical laws/constraints into ML models | PINNs mostly *solve/constrain PDEs* — not built for on-station AWS fault-vs-weather calls; heavier than a real-time QC budget allows | Conceptual lineage for our deterministic thermodynamic engine (Magnus-Tetens), which is lighter and runs in-budget |
| **Sensor-fault-vs-event discrimination in WSNs** — Krishnamachari & Iyengar (2004); Sharma, Golubchik & Govindan (2010, *ACM TOSN*) | Uses **spatial correlation** to separate real "events" from isolated sensor faults; taxonomises fault types (spike / noise / constant) | Generic WSN, **not meteorology-specific**: no thermodynamics, no self-heal; largely academic prototypes, not integrated operational systems | This is the closest academic precedent to our core idea — and citing it is a *strength*: our spatial-corroboration logic is principled, not ad hoc |

**Honest implication:** the *idea* that spatial correlation separates events from faults is not new
(Krishnamachari 2004). SkyGuard's contribution is bringing that idea into meteorology with real
thermodynamics, a calibrated ensemble, a named-fault taxonomy, self-healing, and explainability —
and doing it in ~5 ms.

---

## 3. What SkyGuard combines that no single prior system does

The novelty is the **integration**, stated as a precise, checkable list:

- **Explicit sensor-fault-vs-genuine-weather verdict.** Prior QC flags "suspect"; SkyGuard decides
  *which kind of abnormal* and treats them oppositely — repair the fault, preserve the weather. This
  is the single most expensive error mode in an operational met network, and it is the thing we
  optimise for directly.
- **Physics-thermodynamic reasoning as a first-class, highest-weighted detector** (Magnus-Tetens
  dew point / VPD, WMO gradient limits). It *improves* on real data (50.4% → 78.6% F1) because it
  reasons from first principles rather than learned patterns — the opposite of the learned
  components, which degrade.
- **Four models fused, measured to beat each part.** Not "we used an isolation forest"; a
  weighted consensus whose ablation is published (§4).
- **Root-cause classification with its own confidence** — seven named classes, kept distinct from
  the detection score (`xai/root_cause.py`).
- **Self-healing imputation that quarantines, never deletes,** the original value.
- **Explainability on every reading** (fast additive attributions live; genuine offline SHAP) and
  an exportable audit trail.
- **Honest calibration** — confidence display-capped below 100% with a ± agreement band; headline
  metrics are the real-data ones, not the flattering synthetic ones; limitations written down.
- **Real-time + edge** — ~5 ms/reading, with a C/MicroPython edge build for on-station filtering.

No line item above is unique on its own. The **combination, aimed squarely at the fault-vs-weather
decision, is what is not "already solved" in a single fielded system.**

---

## 4. What we validated against — stated honestly

**The strong, true claim (lead with this):** we validated via **ablation against the standard-method
baselines**, on **real NOAA ISD-Lite historical weather** (real background signal) with the same
controlled faults injected on top. The integrated system beats every standard method run alone:

| Detector (real NOAA data, 6,000 obs) | F1 | AUC |
|---|---|---|
| Physics rule-checker alone | 78.6% | 82.5% |
| EWMA + CUSUM statistical alone | 65.0% | 83.7% |
| Isolation Forest alone | 50.3% | 79.5% |
| Autoencoder alone | 31.3% | 70.4% |
| **SkyGuard integrated (all four + spatial + root-cause)** | **≈ 91.5%** | **97.0%** |

(Headline full-pipeline real-data figure is **~92% F1**; synthetic is 95.7%. The real-data number is
the one to quote — see `docs/PIPELINE_AND_METRICS.md §4`. No train/test leakage: the first 1,530
rows per station are a strict holdout asserted at benchmark time.)

That table *is* a "validated against baselines" story — the baselines being the very methods a
generic anomaly-detection library would give you.

**The candid gap (say it before the judge does):** we have **not yet** reproduced a *named fielded
system* (MADIS / TITAN / Oklahoma Mesonet) on our exact dataset and beaten it head-to-head. Our
comparison is against the standard *methods*, not against a specific product.

**The concrete next step (offer this — it directly answers the question):** run **MET Norway's
`titanlib`** spatial-consistency + buddy check on the identical NOAA replay and report SkyGuard vs.
titanlib on the same faults. titanlib is open-source, Python-callable, and purpose-built for exactly
this — making it the most credible single "previous solution to validate against." This turns the
honest gap into a scoped, achievable deliverable rather than a weakness.

---

## 5. One-paragraph answer you can say out loud

> "The building blocks are prior art and we cite them — WMO and MADIS QC, MET Norway's TITAN for
> spatial checks, the Oklahoma Mesonet QA suite, and standard ML like isolation forests and
> autoencoders. What none of those fielded systems do in one real-time package is make the explicit
> *sensor-fault-versus-genuine-weather* decision: they flag suspect data for a human or for
> assimilation, they don't reason from thermodynamics, name the fault, repair the value, and explain
> the call. That integration is our contribution. For validation, we don't just assert it — we ran
> each standard method alone on real NOAA weather with injected faults and showed the integrated
> system goes from a best-single 79% F1 to about 92%. The honest next step, which we'd genuinely
> value doing, is a direct head-to-head against MET Norway's open-source titanlib on the same data."

---

## References (established literature — verify against the originals before citing formally)

*These are drawn from well-documented, established sources. Live web access was unavailable in the
build environment, so confirm exact titles/years against the publications before putting them in a
formal bibliography.*

- WMO, *Guide to Instruments and Methods of Observation* (CIMO Guide), **WMO-No. 8**.
- WMO, *Guidelines on Quality Control Procedures for Data from Automatic Weather Stations* —
  Zahumenský, I. (2004); related **WMO-No. 305**.
- NOAA MADIS — *Meteorological Assimilation Data Ingest System*, QC documentation
  (`madis.ncep.noaa.gov`).
- MET Norway — **TITAN** and **`titanlib`** (open-source spatial QC library; `github.com/metno/titanlib`).
- Shafer, M. A., Fiebrich, C. A., Arndt, D. S., Fredrickson, S. E., & Hughes, T. W. (2000).
  "Quality Assurance Procedures in the Oklahoma Mesonetwork." *J. Atmos. Oceanic Technol.*
- Dunn, R. J. H., et al. (2012, 2016). HadISD automated QC. *Climate of the Past.*
- Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). "Isolation Forest." *IEEE ICDM.*
- Sakurada, M., & Yairi, T. (2014). "Anomaly Detection Using Autoencoders with Nonlinear
  Dimensionality Reduction."
- Malhotra, P., et al. (2015). "Long Short Term Memory Networks for Anomaly Detection in Time Series."
- Hundman, K., et al. (2018). "Detecting Spacecraft Anomalies Using LSTMs …" *KDD.*
- Krishnamachari, B., & Iyengar, S. (2004). "Distributed Bayesian Algorithms for Fault-Tolerant Event
  Region Detection in Wireless Sensor Networks." *IEEE Trans. Computers.*
- Sharma, A. B., Golubchik, L., & Govindan, R. (2010). "Sensor Faults: Detection Methods and
  Prevalence in Real-World Datasets." *ACM Trans. Sensor Networks.*
- Karpatne, A., et al. (2017). "Theory-Guided Data Science." Raissi, M., et al. (2019). "Physics-
  Informed Neural Networks." *J. Comp. Physics.* Willard, J., et al. — survey on physics-guided ML.
