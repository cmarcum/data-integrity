flowchart TD
  Start([Start]) --> BaseCheck{Baseline exists for each monitored source?}

  BaseCheck -->|No| BaseBuild
  BaseCheck -->|Yes| Scope

  subgraph BaseBuild[Baseline build (T0): pre-processing reference snapshots]
    DG0[Pull full data.gov catalog metadata (CKAN Action API: package_search)] --> DG0snap[Store raw JSON + normalized snapshot AS BASELINE]
    AG0[Pull agency comprehensive inventories (typically agency.gov/data.json)] --> AG0snap[Store raw JSON + normalized snapshot AS BASELINE]

    PRA0[Pull reginfo.gov PRA XML reports (inventory: pending/concluded/expiration/discontinued)] --> ICR0[Normalize + store ICR tables AS BASELINE]
    IDX0[Pull dataindex.us/icr export (CSV download)] --> ICR0

    DG0snap --> Reg0[Initialize dataset registry (canonical IDs + source links + first_seen=T0)]
    AG0snap --> Reg0

    Reg0 --> Dist0[For each baseline distribution URL: HTTP HEAD/GET, redirects, headers]
    Dist0 --> FP0[Compute baseline fingerprints: status, content-type, size, ETag/Last-Modified, SHA-256 when feasible, schema + value-domain summaries]
    FP0 --> Store0[Store fingerprints + deterministic samples AS BASELINE]

    Store0 --> WB0[Wayback lookup for pseudo-baseline: Availability API + CDX listing]
  end

  BaseBuild --> Scope

  Scope{Scope?} -->|Catalog sweep| Sweep
  Scope -->|Specific dataset| Drill

  subgraph Sweep[Run snapshot (Tn): discover + snapshot]
    DG[Pull data.gov catalog metadata (CKAN package_search)] --> DGsnap[Store raw JSON + normalized snapshot AS RUN(Tn)]
    AG[Pull agency inventories (data.json)] --> AGsnap[Store raw JSON + normalized snapshot AS RUN(Tn)]
    DGsnap --> Reg[Update dataset registry (first_seen/last_seen, source links)]
    AGsnap --> Reg
  end

  subgraph Drill[Run snapshot (Tn): specific dataset]
    Input[Input: dataset identifier / URL / title] --> Resolve[Resolve record in data.gov +/or agency data.json]
    Resolve --> Reg2[Build/refresh dataset registry entry]
  end

  Reg --> Dist
  Reg2 --> Dist

  Dist[For each distribution URL (Tn): HTTP HEAD/GET, redirects, headers] --> FP[Compute run fingerprints: status, content-type, size, ETag/Last-Modified, SHA-256 when feasible, schema + value-domain summaries]
  FP --> Store[Store fingerprints + deterministic samples AS RUN(Tn)]

  Store --> WB[Wayback lookup: Availability API + CDX listing]
  WB -->|Change/removal detected| WBCap[Optional capture: Save Page Now for landing pages/docs and (when feasible) file URLs]

  subgraph ICR[ICR monitoring (Tn): collection-change signals]
    PRA[Pull reginfo.gov PRA XML reports] --> ICRstore[Normalize + store ICR tables AS RUN(Tn)]
    IDX[Pull dataindex.us/icr export (CSV)] --> ICRstore
  end

  Reg --> Map[Map datasets ↔ ICRs (OMB Control # / keywords from metadata & docs)]
  ICRstore --> Map

  Store0 --> Diff
  DG0snap --> Diff
  AG0snap --> Diff
  ICR0 --> Diff

  DGsnap --> Diff
  AGsnap --> Diff
  Store --> Diff
  Map --> Diff

  Diff[Diff engine: • data.gov: RUN(Tn) vs BASELINE(T0) + vs RUN(Tn-1) • agency data.json: RUN(Tn) vs T0 + vs Tn-1 • distributions: availability + fingerprint diffs • ICRs: status/expiration diffs] --> Score[Quantify change: severity score + category (incremental + cumulative)]
  Score --> Out[Outputs: change log (JSONL), dataset dossiers, agency summaries, evidence links]
  Out --> End([Complete])