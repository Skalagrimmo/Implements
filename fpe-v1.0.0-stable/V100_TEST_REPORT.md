# FPE v1.0.0 — promotion test report

## Stable promotion gates

- 0.12 → 1.0 semantic parity: **64/64 frozen traces PASS** after normalizing only `runtime_version`;
- fresh-process determinism: **10/10 identical trace SHA-256**;
- public contract: **10 runtime methods / 11 error codes / frozen schema IDs PASS**;
- current snapshot torture: **500/500 exact JSON restore round-trips PASS**;
- historical migration torture: **500/500 0.11/0.12 checkpoint migrations PASS**;
- hostile snapshot torture: **500/500 malformed/future/contradictory checkpoints rejected**;
- exact PixelGen 1.0 cross-engine bridge fuzz: **96/96 worlds PASS**, each before and after an authoritative PixelGen event.

Fresh-process reference trace SHA-256:

```text
5ea35140e4a5808d6e4a20e69471928e6297f104d8364c082b9f3c275cd9da23
```

The exact PixelGen stable archive used for the cross-engine gate had SHA-256:

```text
f24008bd95682164b89d0d49ed346d5ba1a0728ce17a54abdd5fa518167304ee
```

## Retained 0.12 regression/stress gates re-run on 1.0 code

- bridge regression — PASS;
- malformed Python validation — PASS;
- 256 Python↔JavaScript fingerprint parity projections — PASS;
- hierarchy/web core — PASS;
- scheduler replay/rate/fairness/persistence — PASS;
- revision handoff including 1000 replay checks — PASS;
- hierarchy fuzz: **2000 operations PASS**;
- public API/browser-global loading harness — PASS;
- action requests — PASS;
- persistence regression — PASS;
- persistence fuzz: **4500 operations / 460 restores / 790 full-state checks PASS**;
- RC hardening — PASS;
- corruption fuzz: **2400 invalid rejected / 250 valid preserved PASS**;
- extended persistence: **5000 operations / 698 restores / 923 comparisons PASS**;
- large world: **10,000 clusters / 40,000 buds / 11,335,412-byte snapshot / 200 ticks / exact restore PASS**.

The long suites are intentionally runnable as independent chunks because a monolithic wrapper can exceed constrained execution-harness wall-clock limits even when every individual gate passes.

## Manual status

The user reported that the 0.12 RC appeared to work in practical use before promotion. This is useful smoke evidence but is not treated as a formal multi-browser or low-spec performance benchmark. The visual demo still obtains Three.js from CDN; FPE runtime modules themselves have no Three.js dependency.
