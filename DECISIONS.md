# DECISIONS.md (ptat-sim)

Design history and rationale for the PTAT simulation engine and readings interface.
Captures decisions made before any code exists. This document is the source of truth
for _why_ the system is shaped the way it is. ACS conformance depends on it.

---

## D-001. Purpose of this repository

**Status:** Accepted

**Context:**
A team workflow exists for assigning bounded implementation tasks to AI agents. That
workflow requires a pre-built simulation engine and a stable readings interface so that
task assignments can be made against a real contract, not a description. The PTAT sensor
domain was chosen as the first concrete instance of this pattern because it is realistic,
has well-understood anomaly/trend characteristics, and is representative of industrial
monitoring workloads.

**Decision:**
This repository provides two things only: a PTAT readings interface (the contract) and a
simulation engine that produces conforming readings. It does not include test programs,
analysis tools, or dashboards. Those are downstream assignments made against this
interface.

**Consequences:**

- The interface must be stable before any downstream task is assigned
- The sim engine is a dependency, not a deliverable to the end client
- All design decisions about what a reading _is_ happen here, not in downstream repos

---

## D-002. Interface before implementation

**Status:** Accepted

**Context:**
Initial instinct was to generate the full system in one pass. Prior experience showed this
produces coherent but unownable code; correct, but not shaped to team conventions or
decomposed into reviewable units. The alternative (generate → refactor) was also
considered and rejected: refactoring post-generation is cognitively expensive because the
AI's internal consistency works against incremental correction.

**Decision:**
The sequence is: define the `PTATReading` data structure and interface contract first,
then implement the sim engine against it, then assign downstream tasks against the
interface. No implementation begins until the interface is agreed.

**Consequences:**

- Downstream task assignments can specify "implements against PTATReading" rather than
  describing behavior in prose
- The interface is the stable artifact; the sim implementation can be replaced
- This sequence is the repeatable pattern for other domains beyond PTAT

---

## D-003. Design conversation as first artifact

**Status:** Accepted

**Context:**
The adaptive-interfaces stack (ACS, ATD, AO) defines behavioral protocols and skills but
assumes design intent is already encoded somewhere for the agent to conform to. Without a
pre-ACS artifact capturing _why_ the system is shaped the way it is, ACS conformance is
syntactic only. The agent can match structure but not rationale.

**Decision:**
This DECISIONS.md is the first artifact created, before any code, interface definition,
or SKILL.md. It captures the design conversation that preceded all implementation. Future
DECISIONS.md files in other sim/interface repos should follow this pattern.

**Rationale source:**
Design conversation, May 2026. Participants: Denise Case, Claude (Anthropic).

**Consequences:**

- DECISIONS.md becomes the required first artifact for any new sim/interface repo
- ACS has a rationale source to conform to, not just a structural one
- The pattern is documentable and transferable to other teams and domains

---

## D-004. PTAT domain: what we know and what we are learning

**Status:** Active (updated as sim design progresses)

**Context:**
PTAT (Proportional To Absolute Temperature) circuits produce output linearly proportional
to absolute temperature in Kelvin. They appear in semiconductor thermal management,
industrial process monitoring, battery systems, and infrastructure equipment. The client
use case is anomaly detection and trend monitoring. It watches a stream of readings for
deviations from expected behavior.

**What is known at founding:**

- A reading has at minimum: timestamp, sensor identity, temperature value, and status
- Realistic readings include noise (small random variation around true value)
- Trends are slow, directional changes over time (thermal drift, aging, load correlation)
- Anomalies are sudden deviations: spikes, dropouts, stuck values, out-of-range readings
- Multiple sensors in a system can be compared; inter-sensor disagreement is itself a
  signal

**What is being learned as we build:**

- Realistic noise characteristics and magnitude for this sensor class
- Typical sampling rates for monitoring workloads
- Which anomaly types are most diagnostically useful to simulate
- Whether readings carry metadata beyond temperature (voltage, ADC counts, confidence)

**Decision:**
Sim engine will be designed to produce all of: clean readings, noisy readings, trend
sequences, and injected anomalies. The interface will carry enough metadata to
distinguish these in tests without requiring the consumer to inspect implementation.

**Consequences:**

- Interface needs a `scenario` or `mode` field, or a separate factory pattern per type
- Anomaly types become an explicit enumeration, not implicit behavior
- This section is updated as domain knowledge grows during implementation

---

## D-005. Adaptive Interfaces conventions apply

**Status:** Accepted

**Context:**
This repository is being built by a team that uses the adaptive-interfaces stack:
ACS for agent conformance, ATD for tool discovery, AO for onboarding context.

**Decision:**
This repo will include SKILL.md, MANIFEST.toml, and DECISIONS.md following
adaptive-interfaces conventions. When the interface and sim engine are stable, a SKILL.md
will be authored so that AI agents can be onboarded to work against this repo using the
standard ACS → AO workflow.

**Consequences:**

- SKILL.md is a planned artifact, not yet authored (interface must be stable first)
- MANIFEST.toml should be created alongside this file
- Repo structure follows adaptive-interfaces organization patterns

---

## D-006. Source files promoted from adaptive-sensor-testing

**Status:** Accepted

**Context:**
The simulation engine and interface contract were developed in
`adaptive-interfaces/adaptive-sensor-testing` before `ptat-sim` existed
as a dedicated repo. Four files constitute the complete implementation:

| File            | Role                                              |
| --------------- | ------------------------------------------------- |
| `models.py`     | Interface contract; frozen dataclasses, all types |
| `generator.py`  | Scenario implementations against the contract     |
| `data_maker.py` | TOML-driven CSV batch generation CLI              |
| `processor.py`  | Anomaly detection against `ProcessorConfig`       |

**Decision:**
These four files are promoted from
`adaptive-sensor-testing/src/sensor_sim/` into `src/ptat_sim/`
as-is. The package name changes from `sensor_sim` to `ptat_sim`;
internal imports are updated accordingly. No logic changes at
promotion time. Any changes after promotion are recorded as
subsequent decisions.

**Source:**
`https://github.com/adaptive-interfaces/adaptive-sensor-testing`

**Consequences:**

- `adaptive-sensor-testing` becomes a downstream consumer of `ptat-sim`
  rather than the owner of the interface
- Import paths in `adaptive-sensor-testing` update from `sensor_sim`
  to `ptat_sim` after promotion
- `adaptive-sensor-testing/DECISIONS.md` should record this dependency
  change

---

## D-007. MANIFEST.toml schema extensions (proposed)

**Status:** Proposed, pending `adaptive-interfaces-manifest-2` schema update

**Context:**
`adaptive-interfaces-manifest-1` defines repo identity, scope, dependencies,
and provides. It does not define fields for package identity, CLI presence,
docs tooling, or repo-specific release validation steps. These are needed so
an agent can derive `pyproject.toml`, CI workflows, and release procedures
entirely from `MANIFEST.toml` without per-repo decision-making.

**Proposed extensions:**

```toml
[repo]
visibility = "public"
# Drives CI trigger scope and signals CITATION.cff/licensing matter from day one.

[package]
python_name = "ptat_sim"     # drives src/ layout, --cov= target, hatch packages
cli = true                   # drives [project.scripts] and cli.py scaffold
cli_entry = "ptat_sim.cli:main"
cli_description = "Generate synthetic PTAT sensor datasets from TOML config"

[docs]
enabled = true               # drives zensical.toml, docs build step in CI
tool = "zensical"
deploy = true                # drives deploy-zensical.yml workflow

[ci]
link_check = true            # drives links.yml
dependabot = true            # drives dependabot.yml
actionlint = false           # org-level only, not per-repo

[release]
validate_step = "uv run ptat-sim"
# Repo-specific CLI step in CI (E1) and release procedure (Task 2).
changelog_sections = [
  "Notes on versioning and releases",
  "Release Procedure",
  "Links",
]
# Sections appended after version history in every CHANGELOG.

[agent]
conformance = "https://github.com/adaptive-interfaces/adaptive-conformance-specification"
# Behavioral directive: agents MUST apply ACS before generating any artifact.
skill = "SKILL.md"
# Domain operating guide; authored after interface is stable.

[conventions]
source = "https://github.com/structural-explainability/se-constitution"
# ACS scaffold process; what to clone, observe, and conform to.
```

**Decision:**
These fields are used in `ptat-sim` MANIFEST.toml now, marked as proposed.
The `schema` field at the top of MANIFEST.toml remains `adaptive-interfaces-manifest-1`
until the schema is formally updated in `.github/schemas/`.

**Consequences:**

- `.github/schemas/adaptive-interfaces-manifest-1.md` needs a version bump
  and these four section definitions added
- All adaptive-interfaces repos that adopt these fields gain fully
  derivable scaffolds from MANIFEST.toml alone
- This is the mechanism by which MANIFEST.toml becomes the single source
  of truth for repo identity, tooling, and agent behavior

---

_This document grows with the project. New decisions are appended. Existing decisions
are not edited. Superseding decisions reference the one they replace._
