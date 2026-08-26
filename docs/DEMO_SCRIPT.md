# SkyGuard AI — SIH 2026 Demo Script & Talking Points

**Problem Statement 26073 — AI/ML-Based Intelligent Anomaly Detection for Automatic Weather Stations**

This is a presenter's playbook: a setup checklist, a timed screen-by-screen walkthrough with the
exact clicks and lines to say, the three points you must land, and honest answers to the questions
judges actually ask. Everything below can be demonstrated **entirely in the React dashboard** — no
slide-to-app switching mid-demo.

> **The whole pitch in one sentence:** *A weather station can be broken or it can be in a storm —
> both look "abnormal", and telling them apart in real time, with the physics to prove it, is what
> SkyGuard does.*

---

## 0. Before you present — 2-minute setup checklist

- [ ] **Backend running:** `uvicorn backend.app.main:app --reload --port 8000`
- [ ] **Frontend running:** `cd frontend && pnpm dev`, then open **http://localhost:8443**
- [ ] **Confirm the "Live" badge** (top of the Explainable-AI card / status chip). If it says
      **"Demo mode"**, the backend isn't connected — the UI still works on canned data, but live
      injection buttons will be disabled.
- [ ] **Pick a station** in the top-bar selector — start on **Alpha Ridge (AWS_ALPHA_MOUNTAIN)** or
      **Gamma Metropole**.
- [ ] **Clean slate:** if you rehearsed, let the stream run ~15 s so the last injected fault scrolls
      out, or restart the backend.
- [ ] **Second screen / tab (optional but recommended):** `http://127.0.0.1:8000/docs` (Swagger) and
      `benchmark/real_data_evaluation_report.md` — useful for the "is this real?" questions.
- [ ] **Know your timing:** the walkthrough below is ~7 minutes. Practice the spike→thunderstorm
      contrast (Scenes 3–4) until it's smooth — that is the moment that wins the room.

---

## 1. The hook — first 30 seconds

Open on the **Overview** page. Say, roughly:

> "Automatic weather stations feed the forecasts everyone depends on. But a sensor that spikes to
> 54 °C and a genuine thunderstorm rolling in *both* show up as 'abnormal data'. If your system
> cries wolf on the storm, forecasters stop trusting it. If it silently trusts the broken sensor,
> the forecast is wrong. SkyGuard's whole job is to tell those two apart — in real time, and to
> *show its reasoning* — then quietly repair the broken data so the forecast pipeline never sees a
> gap."

Then: *"Let me show you it deciding, live."*

---

## 2. The guided walkthrough

### Scene 1 — Overview: the network at a glance  *(~45 s)*

- Point to the four live station cards streaming Temperature, Pressure, Humidity.
- Point to the **"Fault vs weather · last 24h"** band.

> "Four stations, streaming live. This band is the story in miniature — every anomaly the system saw
> is already sorted into *sensor faults* versus *genuine weather*, with false alarms tracked
> separately. That sorting is the hard part, and it's happening on every single reading."

### Scene 2 — Live Monitor, the calm baseline  *(~45 s)*

Click into **Live Monitor**. Let a few normal readings stream.

- Point to the **Explainable-AI decision card**: verdict reads **NORMAL**.
- Point to the confidence figure.

> "Right now everything's normal. Notice the confidence never reads a flat 100% — it shows a value
> with a ± band. That's deliberate: a calibrated detector shouldn't claim absolute certainty it
> hasn't earned. We'll come back to that."

Leave the **Anomaly injection sandbox** (the row of six buttons) visible — that's your control panel.

### Scene 3 — Inject a SENSOR FAULT: the money moment, part 1  *(~90 s)*

Click **"Temp spike (+15 °C)"**.

Watch the decision card flip and **latch** (it holds the event with a "Held · time" chip so you can
talk over it — the stream keeps moving underneath).

Walk the card top to bottom:

- **Verdict:** now **SENSOR FAULT**.
- **Three-test evidence grid:** Physics ✗ / **Spatial ✗ (isolated — no neighbour shares it)** / Rate ✗
  (exceeds the WMO gradient limit).
- **Root cause readout:** *Sensor spike · Electrical Transient / Sensor Glitch*, with the
  **classifier's own confidence** shown next to it.
- **Neighbour strip:** only the subject station moved; peers are flat.
- **Self-healing:** the raw value is quarantined and the stream shows a **healed** replacement.

> "One button, a +15° spike. The system says *sensor fault* — and here's *why*, not just a score:
> it's physically implausible at that rate, and critically, **no neighbouring station sees it**. A
> real heatwave doesn't hit one thermometer and spare the one next to it. It names the fault type —
> a sensor spike, an electrical transient — and notice this confidence is the *classifier's* own,
> separate from the detection score. Then it repairs the reading so the forecast pipeline never
> chokes on the gap — but it *quarantines* the original, never deletes it."

### Scene 4 — Inject GENUINE WEATHER: the money moment, part 2  *(~90 s)*

Now click **"Thunderstorm (0% false alarm)"** (the indigo button).

> "Same system, same stream — now a real storm."

Walk the contrast:

- **Verdict:** **GENUINE WEATHER**, not fault.
- **Evidence grid:** the change is *coordinated and physically consistent* — temperature drops while
  humidity climbs and pressure moves together, the way a real gust front behaves.
- **Root cause:** *Genuine extreme weather · Atmospheric Convective Storm / Cold Front*.
- **Self-healing:** **not** healed — the readout says *"real signal preserved."*

> "This is the whole product in one contrast. A naive detector flags *both* the spike and the storm
> as 'anomalies' and treats them the same. SkyGuard reaches the **opposite** verdict on the two,
> because it reasons from thermodynamics and from what the neighbours see — and it refuses to
> 'heal' real weather into a smooth lie. That difference is the single most expensive mistake in an
> operational met network, and it's the one we set out to solve."

*(Power move, if you have a second station handy: switch stations in the top bar and inject the
thunderstorm again — now two stations corroborate, and the Map in Scene 5 lights up the coordinated
arc.)*

### Scene 5 — Map: seeing corroboration  *(~45 s)*

Open **Map**.

- An **isolated fault** shows a pulsing dashed **halo** on the single affected pin.
- A **corroborated weather event** draws a soft **arc** linking the stations that agree.

> "This is the spatial logic made visual. Isolation rings a single alarm; corroboration draws the
> connection. On a dense real mesonet this is where the system gets even stronger."

### Scene 6 — Anomalies: triage and the audit trail  *(~40 s)*

Open **Anomalies**.

- The table lists events with their verdict; filter by **Sensor fault** vs **Genuine weather**.
- Click a row → the **decision drawer** shows the same verdict → pipeline → neighbours → healing →
  diagnostic, frozen for that event.
- Point to **Export CSV**.

> "Every decision is logged and exportable — a full audit trail an operator can hand to a
> meteorologist. Nothing is a black box."

### Scene 7 — Analytics: the honest numbers  *(~40 s)*

Open **Analytics**.

> "And we hold ourselves to real numbers. These aren't measured on data we generated and then
> graded ourselves on — they're from replaying **real NOAA historical weather** and injecting faults
> on top. Around **92% F1 on real data**, with the false-alarm rate measured against genuine, un-
> injected weather. Per-fault-type recall is broken out here too — we show the weak spots, not just
> the wins." *(Quote the exact figures shown on your screen / in `benchmark/real_data_evaluation_report.md`.)*

*(Optional — Maintenance: the Sensor Health Index and service advisory. Be precise: "a heuristic
health tracker of present condition, not a trained failure-prediction model.")*

---

## 3. The three things you must make sure you say

1. **Fault vs. weather is the real problem.** Anyone can flag an outlier. Telling a broken sensor
   from a real storm — and being *right* about which to trust and which to repair — is the value.
2. **It reasons, it doesn't just score.** Physics (Magnus-Tetens thermodynamics) + a four-model
   ensemble + cross-station spatial consistency + a root-cause classifier + explainability. The
   physics component is the highest-precision part and *improves* on real data because it reasons
   from first principles rather than learned patterns.
3. **Honesty is a feature.** Confidence is capped below 100% with a ± band; headline metrics are the
   real-data ones, not the flattering synthetic ones; limitations are written down. This is what a
   system that might trigger a maintenance dispatch *should* look like.

---

## 4. Anticipated judge questions — honest answers

**"Why is the confidence never 100%?"**
> Deliberate. The number you see is display-capped just below 100% and annotated with a ± band
> derived from how much the four detectors agree. A finite-evidence statistical detector hasn't
> earned literal certainty, and showing "100%" would invite misplaced trust. The underlying ensemble
> math is untouched — this is an honesty choice in the presentation layer.

**"Is this real machine learning, or just if-statements?"**
> Both, by design, and that's the point. Four components: a deterministic physics engine, an adaptive
> statistical filter (EWMA + CUSUM), an unsupervised Isolation Forest, and a PyTorch temporal
> autoencoder. They fail on *different* inputs, so the ensemble beats every one of them alone —
> ~78% F1 for the best single model on real data versus ~92% combined.

**"Real data or synthetic? Did you grade your own homework?"**
> We caught ourselves doing exactly that and fixed it. The headline numbers come from replaying
> **real NOAA ISD-Lite history** (about 46,000 observations across four real stations) as the clean
> background, then injecting controlled faults. The first ~1,530 rows of every station are a strict
> holdout the learned models are forbidden to train on, asserted at benchmark time so the windows
> can't drift. Everything is seeded and reproducible.

**"What's actually novel versus an off-the-shelf anomaly-detection library?"**
> The fault-versus-genuine-weather discrimination, driven by physics + spatial corroboration, and the
> refusal to "heal" real weather. A generic library gives you an outlier score; it can't tell you the
> storm is real and the spike is not, and it would happily smooth a real gust front into garbage.

**"How does the root-cause classification work?"**
> A rule matrix over the physics, statistical, and spatial signals maps each anomaly to one of seven
> classes — normal, genuine extreme weather, sensor spike, flatline, calibration drift, physical
> inconsistency, communication dropout — each with its own confidence. The dashboard shows that class,
> its engineering category, and that confidence, kept distinct from the detection score.

**"Does it run on real hardware / at scale?"**
> Per-reading latency is ~5 ms, so it's comfortably real-time. There's also an ultra-light C/MicroPython
> edge build (`edge/`) meant for on-station ESP32-class filtering. Honest caveat: the C header is
> behaviourally matched to the Python but hasn't been compiled on-device yet — we call that out.

**"What are its weaknesses?"**
> Three, plainly: self-healing imputation degrades over long outages because it isn't yet diurnal-
> aware; calibration drift is the hardest fault class (~85% recall) because slow drift and slow real
> weather are genuinely hard to separate from one station alone; and our four demo stations are
> continents apart, so the spatial check only *loosens* the weather gate and never tightens on
> isolation — it gets much stronger on a dense local mesonet.

**"If the only nearby station is the broken one, does spatial logic still help?"**
> Less so — that's the limitation above. In that case the decision leans on physics and temporal
> reasoning, which is why physics carries the highest ensemble weight. Spatial corroboration is an
> amplifier, not a crutch.

**"What did you build versus glue together?"**
> The physics engine, the ensemble and its weighting, the root-cause classifier, the spatial-
> consistency logic, the self-healing imputer, the benchmark harness, and both UIs. The learned
> models use PyTorch and scikit-learn; the reasoning around them is ours.

---

## 5. If something breaks — recovery

- **"Demo mode" badge / injection buttons greyed out:** the backend isn't reachable. Either restart
  `uvicorn`, or lean in — *"the dashboard degrades gracefully to demo data rather than showing a dead
  screen"* — and narrate the canned decision card, which shows the same structure.
- **Injection does nothing:** confirm a station is selected and the badge says **Live**; the buttons
  act on the *currently selected* station.
- **Total frontend failure:** fall back to the second tab — open Swagger (`/docs`), hit
  `POST /api/inject_anomaly`, and show the raw processed packet, then show the benchmark reports.
  The story survives without the pretty UI.

---

## 6. Closing line

> "SkyGuard doesn't just flag that something's wrong — it decides *whether* it's wrong, proves *why*,
> fixes the data, and tells you honestly how sure it is. That's the difference between an alarm and a
> system a forecaster will actually trust."
