# ROS Duty Cycle Near Neuronal Microtubules for an O₂•⁻→Tryptophan Radical-Pair Transduction Chain

## Executive summary
Baseline *steady-state* intracellular superoxide (O₂•⁻) is widely argued to be extremely low—often quoted around ~10⁻¹⁰ M (~0.1 nM)—because superoxide dismutases (SODs) remove O₂•⁻ at near–diffusion-limited rates. citeturn1search0turn16view0turn19view0 Direct “local microtubule-adjacent O₂•⁻ concentration” measurements at 100–500 nm scales in neurons are scarce; most methods either report bulk/compartment averages or detect downstream oxidants (notably H₂O₂) with better tractability. citeturn1search25turn3search13turn19view0
A physically realistic way to bound microdomain O₂•⁻ is to combine (i) neuronal oxygen use per neuron, (ii) realistic mitochondrial electron-leak fractions to ROS (often much less than the commonly repeated 1–4%), and (iii) reaction–diffusion with SOD-mediated clearance. citeturn15view0turn7search1turn16view0turn17search0turn3search3 Under conservative assumptions consistent with those sources, sustained **≥10 nM cytosolic O₂•⁻ at 100–500 nm from a mitochondrion** looks *unlikely* in healthy baseline physiology and becomes plausible mainly during **episodic high-ROS regimes** (e.g., hypoxia/reoxygenation “flash-like” mitochondrial ROS bursts, strong NMDAR/NOX2 activation, seizure-like hyperexcitability, ischemia-reperfusion). citeturn11view0turn5view0turn23view0  
A defensible, literature-constrained conclusion is that **the NFT chain is more likely episodic than continuously available**—with a “≥10 nM local O₂•⁻” duty cycle that is probably **well under 1% during ordinary cortical processing**, but can plausibly rise to **minutes-scale windows** during acute metabolic/ionic stress (raising the duty cycle to **several percent or higher** in those episodes). citeturn11view0turn23view0turn5view0

## What the primary literature really constrains
Two things are unusually solid (and frequently confused):

First, SOD chemistry makes O₂•⁻ intrinsically hard to accumulate. Spontaneous dismutation at neutral pH is ~5×10⁵ M⁻¹s⁻¹, but SOD-catalyzed dismutation is reported near **k ≈ 1.6×10⁹ M⁻¹s⁻¹** (approaching diffusion-limited). citeturn16view0 This means that in any microdomain where SOD is present at micromolar concentrations, O₂•⁻ lifetimes are expected to be short (sub-ms to ms) and concentrations strongly production-limited.

Second, the oft-repeated statement that **1–4% of mitochondrial oxygen consumption becomes ROS in vivo** is criticized as an artifact of “maximizing” conditions (e.g., antimycin A, saturated substrates/O₂). A more realistic figure discussed in mitochondria-focused work is substantially smaller; one cited estimate under “less unrealistic” conditions is **~0.15%**. citeturn7search1 This matters: any transduction argument that needs order-of-magnitude higher O₂•⁻ than baseline must reconcile with that constraint unless it invokes *localized bursts*.

The key gap relative to your requested deliverables is that **few papers report absolute O₂•⁻ concentrations in neuron sub-µm microdomains**; instead, many report *relative* changes via dyes, or they measure H₂O₂ (which is more stable and membrane-permeant) as the tractable redox signal. citeturn1search25turn19view0

## Baseline O₂•⁻: bulk levels and the “10 nM” threshold implication
A widely used order-of-magnitude for steady-state superoxide is **~10⁻¹⁰ M (~0.1 nM)**, explicitly stated in peer-reviewed work discussing why SOD keeps O₂•⁻ low. citeturn1search0turn24search2 This aligns with your “0.1–1 nM” baseline framing, but it also shows why a sustained 10 nM regime is nontrivial: it is already **~100× above a commonly cited steady-state**.

A practical point: much of neuronal “ROS signaling” literature is functionally consistent with **H₂O₂ (nM)** as a second messenger rather than O₂•⁻, because H₂O₂ is longer-lived and can diffuse/transport further. citeturn3search24turn19view0 So, if NFT’s transduction chain is specifically O₂•⁻-limited, you should expect strong pressure toward episodic availability (bursts) unless you can show a dedicated microtubule-adjacent O₂•⁻ source that bypasses SOD and avoids rapid conversion to H₂O₂.

## Local microdomains between mitochondria and microtubules: what we can infer (with numbers)
### Proximity premise
In neurons, mitochondria are actively positioned and transported along microtubules via kinesin/dynein adaptor systems, and they are enriched near high-demand sites (synapses, branch points). citeturn21search24turn12search15turn21search2 Even without pinning an exact “100–500 nm mitochondrion↔microtubule gap” number, neuronal geometry makes it plausible that many microtubules pass within submicron distances of mitochondria.

### Clearance-limited diffusion: an upper bound on how far O₂•⁻ can matter
One can bound the spatial reach of O₂•⁻ by combining:
- a diffusion coefficient in water for O₂⁻ estimated around **8×10⁻⁵ cm²/s** (≈8×10⁻⁹ m²/s) citeturn17search0turn17search4  
- SOD-catalyzed removal near **1.6×10⁹ M⁻¹s⁻¹** citeturn16view0  
- a rough CNS SOD1 abundance: **~100 μg/g wet weight in human CNS** citeturn3search3  

If one converts 100 μg/g wet weight of SOD1 to a molar tissue concentration (order-of-magnitude), it lands around a few micromolar (≈3 μM for a ~32 kDa dimer), implying a pseudo-first-order removal rate **k’ ≈ (1.6×10⁹)(3×10⁻⁶) ≈ 5×10³ s⁻¹**, i.e. a characteristic lifetime on the order of **~0.2 ms**. citeturn16view0turn3search3

That lifetime combined with the diffusion coefficient corresponds to a characteristic diffusion distance on the order of **~1 μm** (order-of-magnitude). (This is a model-based inference from cited parameters, not a direct in vivo measurement.) citeturn17search0turn16view0turn3search3

Implication for your microdomain question: **100–500 nm sits inside this “could be reached” zone**, *if* O₂•⁻ is produced on the cytosolic side at sufficiently high flux and not instantly converted inside the organelle before exit.

### How large a cytosolic O₂•⁻ flux is needed to reach 10 nM at 100–500 nm?
If we approximate a point-like source emitting O₂•⁻ into cytosol, a steady-state diffusion estimate gives the required cytosolic-source strength to maintain **10 nM at ~100 nm** as on the order of **Q ~ 10⁵ molecules/s** (and several ×10⁵ molecules/s at ~500 nm), before accounting for additional first-order decay. (This is a back-of-the-envelope physics bound, but it is anchored by measured D and SOD kinetics above.) citeturn17search0turn16view0turn3search3

Now compare to constraints on total mitochondrial ROS production. A cross-species metabolic analysis reports **oxygen consumption per neuron** values; for humans, the table shows an O₂ use per neuron on the order of ~10⁻¹⁰ ml/min. citeturn15view0 If only ~0.15% of that oxygen flux becomes superoxide/H₂O₂ in realistic conditions, the *total* ROS equivalent production per neuron is on the order of **10⁵–10⁶ molecules/s** (order-of-magnitude). citeturn7search1turn15view0  

But that is neuron-wide and includes matrix-side production that may not appear as **cytosolic O₂•⁻**. Therefore, achieving **10 nM O₂•⁻ specifically in the cytosolic microtubule-adjacent microdomain** likely requires **highly localized, bursty export** (a small subset of mitochondria or specific membrane oxidases that generate O₂•⁻ directly into the relevant compartment).

## Peaks and time-courses: what “bursty O₂•⁻” looks like in primary sources
Two calcium-/activity-linked ROS phenomena from primary literature are useful as temporal anchors:

### Mitochondrial “superoxide flashes” (bursts on ~10-second scale)
A landmark single-organelle imaging study reported **stochastic, localized bursts (“superoxide flashes”)** with a typical rise time of **~3.5 s** and decay half-time of **~8.6 s**, i.e., about **10 seconds** per event. citeturn10view0turn11view0 In the same paper, **primary cultured hippocampal neurons** showed flash activity, and the reported flash incidence for hippocampal neurons was **~31 ± 4 events per 1000 μm² cell area per 100 s** (with the paper emphasizing cell-type variation). citeturn11view0  

Crucial caveat: these flashes are detected in the **mitochondrial matrix**. The authors argue that because matrix O₂•⁻ can convert to membrane-permeant H₂O₂, such discrete events could create *ROS microdomains* near mitochondria. citeturn11view0 Whether they create **cytosolic O₂•⁻ microdomains** at ≥10 nM depends on export mechanisms and local SOD; this remains uncertain.

Additional caveat (important for credibility): the interpretation of cpYFP-based “flash” signals has been debated because cpYFP is pH-sensitive, and some reviews argue “flashes” can reflect pH transients rather than O₂•⁻ bursts, or a mixture. citeturn9search5turn9search19 For duty-cycle arguments, this means you should treat flash frequency as **evidence for intermittent mitochondrial events consistent with redox transients**, but not as a clean direct readout of cytosolic O₂•⁻ concentration.

### NOX2-linked neuronal superoxide under strong excitatory drive (minutes to tens of minutes)
A widely cited neuron study showed that NMDA receptor activation induces a **rapid increase** in superoxide-linked fluorescence (via dihydroethidium oxidation products), with the signal **plateauing after ~20–30 minutes**, and it provided genetic/pharmacologic evidence that neuronal **NADPH oxidase (NOX2)** is the primary source under those conditions. citeturn5view0turn1search7 This places one class of “high superoxide regime” (at least by proxy) on **minute to tens-of-minutes** time scales. It is, however, closer to *pathological/excitotoxic* stimulation than ordinary 1–20 Hz cortical firing, so it should not be used as a baseline-duty-cycle proxy without that qualification.

### Seizure-like hyperexcitability: two-phase ROS on minute scales
In a seizure-like activity model (low-Mg²⁺), neuronal ROS generation rises on **minutes** time scales, and mechanistically the paper identifies **NADPH oxidase** in early phases and **xanthine oxidase** contributing later (with mitochondrial ROS not being the main contributor under their measured conditions). citeturn23view0 This is highly relevant to your “physiological duress” framing: it supports the idea that during hyperexcitable/energy-stressed states, neurons can enter episodic high-ROS windows lasting **many minutes**, consistent with a non-negligible duty cycle in those regimes.

## SOD and antioxidant buffering: what controls whether microdomains exceed bulk
The core quantitative control is the pseudo-first-order removal rate **k’ = k[SOD]**.

- The SOD-catalyzed dismutation rate constant is reported around **1.6×10⁹ M⁻¹s⁻¹** (bovine enzyme across a broad pH span in one review’s summary). citeturn16view0  
- Human CNS SOD1 abundance is reported at ~**100 μg/g wet weight** in multiple CNS regions. citeturn3search3  
- SODs’ very high catalytic efficiency plus their abundance is a major reason the field repeatedly cautions that superoxide is difficult to use as a long-range signal (and why measurement is difficult). citeturn19view0turn1search25  

This implies that to sustain **≥10 nM O₂•⁻** locally you typically need one (or more) of:
- a **very high local production flux** (burst) in the immediate vicinity of the target, or  
- **local reduction of effective dismutation capacity** (transient SOD saturation/inhibition, altered metalation states, redistribution), or  
- production in a **partially secluded compartment** with different scavenger composition (though microtubule-adjacent cytosol is generally not secluded the way membranes are).

For a duty-cycle computation, SOD matters because it sharply limits the *persistence* of O₂•⁻ after production stops; even if bursts are strong, O₂•⁻ is expected to fall back toward baseline quickly once production drops. citeturn16view0turn19view0

## Duty cycle estimate for local ≥10 nM O₂•⁻ near microtubules
### What can be stated with high confidence
The primary literature strongly supports that:
- “continuous” bulk cytosolic superoxide at ~10 nM would be atypically high compared to commonly cited steady-state values, and is inconsistent with the general picture of SOD-controlled low O₂•⁻. citeturn1search0turn16view0turn19view0  
- neurons can enter **episodic high-ROS windows** under strong excitation/metabolic stress on **seconds-to-minutes** scales (mitochondrial flash-like events; NOX2/XO-mediated phases in hyperexcitability; NMDA/NOX2 paradigms). citeturn11view0turn23view0turn5view0  

So: the mechanism being **episodically available** is more consistent with the evidence than being continuously available.

### A conservative, literature-anchored quantitative bound (with explicit assumptions)
To turn your “10 nM needed” threshold into a duty-cycle number, you need at least one link that is currently missing from the literature: a calibrated mapping from neuronal activity/metabolic state → **local cytosolic O₂•⁻ at microtubule distance scales**. Because that mapping is not well measured, the most defensible estimate is a range anchored by two regimes:

**Regime 1: ordinary baseline / routine spiking (likely <10 nM)**
Using (i) oxygen-per-neuron numbers (human: ~10⁻¹⁰ ml/min per neuron), (ii) realistic mitochondrial ROS fractions (~0.15% rather than 1–4%), and (iii) the fact that much mitochondrial O₂•⁻ is generated matrix-side and quickly dismutated, the *expected* cytosolic O₂•⁻ at 100–500 nm from mitochondria during routine operation is plausibly on the order of the commonly cited **sub-nM** steady-state, not 10 nM. citeturn15view0turn7search1turn16view0turn19view0  
**Practical duty-cycle inference:** during ordinary cortical processing, time spent ≥10 nM locally is plausibly **near zero to a small fraction of time** (≪1%), unless there exist undocumented microtubule-adjacent O₂•⁻ sources or strong microdomain confinement.

**Regime 2: duress / high-ROS episodes (can plausibly exceed 10 nM locally)**
During hyperexcitability and metabolic stress, literature demonstrates **minute-scale phases** of ROS production driven by NADPH oxidase and xanthine oxidase, and seconds-scale flash-like mitochondrial events. citeturn23view0turn11view0 These conditions are plausible candidates for transient excursions into “≥10 nM local O₂•⁻” regimes, especially near the producing membranes/organelles.

**Practical duty-cycle inference:** if a neuron experiences (for example) a few tens of seconds to minutes per hour in such high-ROS episodes (not implausible under intermittent stressors, high-demand bursts, or subclinical hypoxia-like fluctuations), the effective duty cycle could be **~0.1–5%**, with **larger values** in pathological states (ischemia-reperfusion, seizures, excitotoxicity) where the literature reports sustained ROS generation on minute scales. citeturn23view0turn5view0turn11view0  

**Bottom-line estimate (defensible as a range, not a point):**
- **Healthy routine cognition:** **≪1%** of active time with microtubule-adjacent O₂•⁻ ≥10 nM (likely *episodic and rare*). citeturn1search0turn16view0turn19view0  
- **Acute high-demand/duress periods (hypoxia/reoxygenation-like transitions, seizure-like hyperactivity, strong NMDAR/NOX2 activation):** **minutes per hour** are plausible, i.e. **~1–10%** duty cycle during those periods (and near 0% outside them). citeturn23view0turn11view0turn5view0  

I’m explicitly flagging that the “≥10 nM at microtubule distance” part is **model-inferred**; the primary literature supports the *episodic ROS* picture robustly, but does not yet provide a clean, calibrated microdomain O₂•⁻ concentration time series in neurons.

## Measurement caveats and what experiments would actually settle this
The strongest caveat for your literature review is methodological: **many widely used superoxide probes are not strictly specific in cells**, and fluorescence readouts are seldom calibrated to absolute concentration in nM in situ. The field has repeatedly emphasized best practices and pitfalls. citeturn1search25turn3search13turn19view0

To make this transduction-chain question scientifically crisp, you want experiments that directly measure **local O₂•⁻ (or a validated proxy convertible to O₂•⁻ flux)** near microtubules at ~100–500 nm, with temporal resolution sufficient to resolve second-to-minute bursts. The most credible “next-step” measurement stack suggested by the methodological literature would be:
- **Validated DHE chemistry**: measure **2-hydroxyethidium** (the superoxide-specific product in cell-free conditions) with **HPLC/LC-MS** rather than relying on bulk fluorescence alone. citeturn3search13turn6search34  
- **Targeted spatial sampling**: combine super-resolution localization of mitochondria↔microtubule geometry with local ROS readouts (recognizing the diffraction limit issue and probe perturbations). citeturn1search25turn21search2  
- **Stimulus protocols** that bracket regimes:
  - routine firing-like stimulation vs
  - high-frequency/burst firing vs
  - metabolic stressors (hypoxia/reoxygenation, high workload) that are known to elevate ROS microdomain activity. citeturn11view0turn23view0  
- **Intervention**: manipulate SOD capacity (genetic/chemical) cautiously to test whether local O₂•⁻ microdomains are SOD-limited, without creating artifactual oxidative pathology. citeturn19view0turn16view0

If you get even one robust dataset of “microtubule-adjacent O₂•⁻ time series” showing time-above-threshold at ≥10 nM under physiological firing patterns, it would transform the duty-cycle argument. Conversely, if carefully calibrated assays show that cytosolic O₂•⁻ remains sub-nM except under pathology, that would force NFT’s bottleneck to be explicitly “stress-gated” (episodic consciousness availability) or to pivot toward H₂O₂/redox signaling rather than O₂•⁻ itself. citeturn19view0turn3search24

## Primary-source reference list
Juarez et al., 2008 (discussion of SOD1 maintaining low steady-state superoxide ~10⁻¹⁰ M). citeturn1search0  
Murphy et al., 2022 (consensus guidelines for ROS measurement and nomenclature). citeturn1search25  
Fernandes et al., 2007 (DHE oxidation products; specificity limitations; HPLC-based analysis). citeturn3search13  
Fujii et al., 2022 (rate constants for spontaneous vs SOD-catalyzed superoxide dismutation; biochemical constraints). citeturn16view0  
Leykam et al., 2025 (SOD1 protein content in human CNS). citeturn3search3  
Li et al., 2009 (diffusion coefficient estimate for O₂⁻ in water). citeturn17search0turn17search4  
Brand, 2010 (critique of 1–4% ROS diversion; discussion of ~0.15% under more realistic conditions). citeturn7search1  
Herculano-Houzel, 2011 (oxygen use per neuron; compiled in BNID table). citeturn15view0  
Wang et al., 2008 (mitochondrial “superoxide flashes,” ~10 s events; hippocampal neuron flash incidence; reoxygenation effects). citeturn10view0turn11view0  
Schwarzländer et al., 2012 and Wei-LaPierre et al., 2013 (debate/validation around cpYFP flash interpretation and pH confounds). citeturn9search5turn9search19  
Brennan et al., 2009 (NMDA-induced neuronal superoxide; NOX2 as primary source; plateau ~20–30 min). citeturn5view0  
Kovac et al., 2014 (seizure-like activity induces ROS; NADPH oxidase and xanthine oxidase contributions; minutes-scale phases). citeturn23view0