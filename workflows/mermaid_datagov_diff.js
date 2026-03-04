%% This mermaid.js flowchart describes a replicable process for 
%% monitoring changes to federal open government data, including
%% changes to ICRS. The workflow makes use of non-governmental 
%% tools including dataindex.us, the WayBackMachine, and custom 
%% python routines. 
%% 
%% Last updated: 3.2.2026

%%{init: {'flowchart': {'rankSpacing': 80, 'nodeSpacing': 50}}}%%
 
flowchart TD
  Start([Start]) --> BaseCheck{"Baseline exists for each monitored source?"}

  BaseCheck -->|No| BaseBuild
  BaseCheck -->|Yes| Scope

  %% -------------------------
  %% Baseline build (T0)
  %% -------------------------
  subgraph BaseBuild ["Baseline build (T0): pre-processing reference snapshots"]
    %% Tool-native baseline capture
    HS0["CLI: list-harvest (Data.gov harvest sources)"] --> HS0snap["Store harvest sources JSON AS BASELINE"]
    DG0["CLI: snapshot-org (Data.gov CKAN via package_search)"] --> DG0snap["Store raw org snapshot JSON AS BASELINE"]
    AG0["CLI: fetch-datajson (agency inventory feed)"] --> AG0snap["Store raw data.json (+ fetch_meta) AS BASELINE"]

    %% Optional: normalized views (your existing normalization step)
    DG0snap --> DG0norm["Normalize Data.gov snapshot AS BASELINE"]
    AG0snap --> AG0norm["Normalize agency inventory AS BASELINE"]
    HS0snap --> HS0norm["Normalize harvest sources AS BASELINE"]

    %% Registry initialization (your design)
    DG0norm --> Reg0["Initialize dataset registry canonical IDs + source links + first_seen=T0"]
    AG0norm --> Reg0

    %% Distribution baselines (adjacent routines)
    Reg0 --> Dist0["For each baseline distribution URL: HTTP HEAD/GET, redirects, headers"]
    Dist0 --> FP0["Compute baseline fingerprints: status, content-type, size, ETag/Last-Modified, SHA-256 when feasible, schema/value-domain summaries"]
    FP0 --> Store0["Store fingerprints + deterministic samples AS BASELINE"]

    %% Wayback pseudo-baseline evidence (tool-native CDX query; optional availability checks)
    Store0 --> WB0["CLI: wayback-cdx (pseudo-baseline CDX listing)"]
  end

  BaseBuild --> Scope

  %% -------------------------
  %% Monitoring scope
  %% -------------------------
  Scope{"Scope?"} -->|"Full Catalog"| Sweep
  Scope -->|"Specific dataset"| Drill

  %% -------------------------
  %% Run snapshot (Tn): discover + snapshot
  %% -------------------------
  subgraph Sweep ["Run snapshot (Tn): discover + snapshot"]
    HS["CLI: list-harvest"] --> HSsnap["Store harvest sources JSON AS RUN(Tn)"]
    DG["CLI: snapshot-org"] --> DGsnap["Store org snapshot JSON AS RUN(Tn)"]
    AG["CLI: fetch-datajson"] --> AGsnap["Store agency data.json AS RUN(Tn)"]

    %% Registry updates (your design)
    DGsnap --> Reg["Update dataset registry first_seen/last_seen + source links"]
    AGsnap --> Reg
  end
  
  %% -------------------------
  %% Cross-Check Routine
  %% -------------------------
  AGsnap --> SyncCheck["CLI: cross-check (Compare AGsnap vs DGsnap for sync issues)"]
  DGsnap --> SyncCheck
  SyncCheck --> SyncOut["Ingestion Gap Report: Missing from Data.gov & Stale Ghost Records"]
  SyncOut --> Out

  %% -------------------------
  %% Run snapshot (Tn): specific dataset
  %% -------------------------
  subgraph Drill ["Run snapshot (Tn): specific dataset"]
    Input["Input: dataset identifier / URL / title"] --> Resolve["Resolve record in Data.gov and/or agency data.json"]
    Resolve --> Reg2["Build/refresh dataset registry entry"]
  end

  Reg --> Dist
  Reg2 --> Dist

  %% -------------------------
  %% Distribution checks (Tn)
  %% -------------------------
  Dist["For each distribution URL (Tn): HTTP HEAD/GET, redirects, headers"] --> FP["Compute run fingerprints: status, content-type, size, ETag/Last-Modified, SHA-256 when feasible, schema/value-domain summaries"]
  FP --> Store["Store fingerprints + deterministic samples AS RUN(Tn)"]

  %% Wayback evidence & content drift check (tool-native compare-wayback)
  Store --> WB["CLI: wayback-cdx (capture listing) + replay URL evidence"]
  WB -->|"High-signal URL or changed fingerprint"| WBCompare["CLI: compare-wayback (live vs latest Wayback capture) hash + size + CSV/JSON lightweight structure diffs"]
  WBCompare --> WBResult{"Wayback capture exists?"}
  WBResult -->|No| NoCap["Record: no capture evidence log CDX query + target URL"]
  WBResult -->|Yes| DiffCap{"Live vs Wayback differ?"}
  DiffCap -->|No| Stable["Record: stable vs archived store capture timestamp + replay URL + hashes"]
  DiffCap -->|Yes| Drift["Record: drift detected hash mismatch and/or CSV/JSON structural mismatch store replay URL + timestamps + hashes"]

  %% Optional preservation action (adjacent; keep as optional)
  Drift --> SaveNow["Optional/Adjacent: Save Page Now (landing pages/docs) (when feasible for file URLs)"]
  NoCap --> SaveNow

  %% -------------------------
  %% ICR monitoring
  %% -------------------------
  subgraph ICR ["ICR monitoring (Tn): collection-change signals"]
    PRA["Adjacent: Pull reginfo.gov PRA XML reports"] --> ICRstore["Normalize + store ICR tables AS RUN(Tn)"]
    IDX["Adjacent: Pull dataindex.us/icr export (CSV)"] --> ICRstore
  end

  Reg --> Map["Map datasets ↔ ICRs (OMB Control # / metadata keywords / docs)"]
  ICRstore --> Map

  %% -------------------------
  %% Diff + scoring + outputs
  %% -------------------------
  %% Baselines into diff engine
  HS0snap --> Diff
  DG0snap --> Diff
  AG0snap --> Diff
  Store0 --> Diff
  ICRstore --> Diff

  %% Runs into diff engine
  HSsnap --> Diff
  DGsnap --> Diff
  AGsnap --> Diff
  Store --> Diff
  Map --> Diff
  WBCompare --> Diff

  Diff["CLIs: diff, diff-inventory, inspect-diff • Harvest sources: RUN(Tn) vs T0/Tn-1 • Data.gov org: RUN(Tn) vs T0/Tn-1 • Agency data.json: RUN(Tn) vs T0/Tn-1 • Distributions: fingerprint diffs + live-vs-Wayback diffs • ICRs: status/expiration/discontinued diffs"] --> Score["Quantify change: severity score + category (incremental + cumulative)"]
  Score --> Out["Outputs: change log (JSONL), dataset dossiers, agency summaries, evidence links (Wayback replay URLs + hashes + timestamps)"]
  Out --> End([Complete])

  %% Optional baseline roll-forward
  End --> Refresh{"Baseline refresh window reached?"}
  Refresh -->|No| Start
  Refresh -->|Yes| Promote["Promote selected RUN(Tn) artifacts to BASELINE (controlled, documented roll-forward)"]
  Promote --> Start