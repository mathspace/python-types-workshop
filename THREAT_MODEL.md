# python-types-workshop threat model

## Overview

This is an educational Python typing workshop. The runnable hello example prints a greeting (`hello.py:1-6`); callable.py demonstrates callback protocols and intentionally incompatible calls (`callable.py:25-41`); new_type.py demonstrates static distinctions and calls with plain integers (`new_type.py:4-16`). The package declares no runtime dependencies and a Python minimum, with basedpyright and Ruff as development tools (`pyproject.toml:1-17`). The lint script deliberately fixes and formats working files (`bin/lint.sh:1-4`). No web server, user identity store, or real authorization system is present. The illustrative create_product snippet in ideas.md:130-159 assigns json.loads output to a TypedDict and passes fields to Product.objects.create without runtime schema validation; it is teaching text, not an implemented endpoint.

| Component / resource | Source |
| --- | --- |
| Teaching examples, including Markdown request/persistence illustration | hello.py:1-6; callable.py:25-41; new_type.py:4-16; ideas.md:130-159 |
| Development tool installation and resolved binary dependency | pyproject.toml:1-17; uv.lock:9-35 |
| Lint mutation | bin/lint.sh:1-4 |

| Deployment or workflow | Resource or capability | Configuration and precedence | Safe effective value or location | Readers, writers, or recipients | Enforcing control | Evidence or unknowns |
| --- | --- | --- | --- | --- | --- | --- |
| Local learner execution | Teaching examples | Python loads checked-out example | hello.py, callable.py, new_type.py; terminal output | Learner process and terminal | Local OS account; examples have no privileged resources | hello.py:1-6; callable.py:25-41; new_type.py:4-16 |
| Local uv environment | Development tool installation | pyproject dev group plus uv.lock resolution; basedpyright depends on nodejs-wheel-binaries | Locked basedpyright 1.31.0 and nodejs-wheel-binaries 22.17.1 with platform wheels, plus Ruff; no runtime dependencies | Developer machine and package suppliers (PyPI/files.pythonhosted.org in lock) | uv cutoff reduces fresh-version exposure; lock records artifact hashes, which bind bytes when honored but do not establish supplier trust; installation not inspected | pyproject.toml:9-17; uv.lock:9-35 |
| Explicit local lint command | Lint mutation | bin/lint.sh → ruff check --fix . → ruff format . | Current working directory tree, not script-relative project root | Developer account and working files | Operator invocation context; no path restriction in script | bin/lint.sh:1-4 |

## Threat Model, Trust Boundaries, and Assumptions

Protected assets: Developer working-tree integrity and tool-execution authority. Correct learner understanding that type annotations are not runtime authentication or validation.

A contributor can propose source/assets and an external package/CDN supplier controls its delivered bytes. These capabilities do not inherently include merge permission or the viewer/developer account. New authority arises only if untrusted bytes are accepted and executed by that consumer.

Third-party development packages and transitive binary artifacts → executable tools in the local environment. uv.lock records basedpyright 1.31.0 depending on nodejs-wheel-binaries 22.17.1, platform wheels and SHA-256 hashes; preserve and review the locked graph and verify selected artifacts, not only direct dependency declarations (pyproject.toml:9-17; uv.lock:9-35).
Lint command → current-directory files: local intended mutation shares the developer’s existing rights, not an external user boundary (`bin/lint.sh:3-4`).
Example type declaration → learner adoption in a future program; the supplied UserId example does not implement access checks (`new_type.py:4-16`). ideas.md:144-155 also crosses from request.body through json.loads to an ORM create call in an illustrative snippet; a TypedDict annotation does not enforce field types, required fields or business/ownership rules. Downstream adopters need runtime validation and authorization before persistence.

Security objectives: Keep educational examples separate from production security claims. Make local mutation scope explicit and review executable dependency changes.

No implemented network listener, persistence store, deployment manifest or secret consumer is established. ideas.md:130-159 illustrates a Django request/persistence boundary but supplies no deployed route or complete Product implementation.
Intentional typing errors are teaching material, not vulnerabilities. No dependency execution or package security review was conducted.

## Attack Surface, Mitigations, and Attacker Stories

These are prioritized threat hypotheses, not validated findings. A scenario requires its stated attacker capability and downstream consumer; absence of implementation evidence is an open question, not proof of a vulnerability.

| Priority | Scenario and capability gain | Prerequisites | Impact | Existing controls | Mitigation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | Malicious development package or transitive binary code runs when a learner installs/uses tooling. | Compromised accepted package/version or dependency-source/lock change and actual execution; includes basedpyright’s nodejs-wheel-binaries supplier. | Local developer account compromise, conditional on supply-chain failure. | No runtime dependencies; uv cutoff is not authentication. Lockfile hashes bind selected artifact bytes when honored, not their safety. | Review the resolved transitive graph and lock changes, verify artifact hashes and package source before execution. | pyproject.toml:7-17; uv.lock:9-35 |
| P2 | Learner runs lint from an unintended directory and changes unrelated files. | Operator chooses wrong working directory; no remote attacker needed. | Bounded local data integrity effect, ordinarily operator-safety issue. | Explicit --fix and format commands make intent visible. | Run in intended checkout and inspect version-control diff. | bin/lint.sh:3-4 |
| P3 | UserId is copied into a real application as though it enforced authorization. | Separate application accepts hostile identifiers and has no ownership check. | Only conditional downstream authorization failure; not present in workshop. | Example explicitly labels static type errors and prints calls. | Keep runtime validation and authorization at consuming application boundaries. | new_type.py:4-16 |
| P3, downstream adoption | A learner copies the TypedDict request example as runtime validation and persists hostile JSON fields. | A separate application exposes the copied handler to untrusted input without schema/business validation or required authorization. | Invalid or unauthorized product/category data or request failures; not an implemented workshop vulnerability. | JSON syntax errors are caught; TypedDict supplies static information, not runtime field validation. | Validate decoded shape, field types/ranges and category entitlement before the ORM write; label the illustrative boundary clearly. | ideas.md:130-159 |

## Severity Calibration (Critical, High, Medium, Low)

| Level | Example | Counterexample or limiting prerequisite |
| --- | --- | --- |
| Critical | Only if an independently demonstrated exploit crosses into catastrophic authority beyond the documented local/browser workflow. | No privileged remote service or mass-compromise deployment is established here. |
| High | Malicious executable dependency or active presentation artifact compromises a sensitive developer account or co-hosted application origin. | Requires actual execution and sensitive authority; a version number or illustrative code fragment does not prove exploitability. |
| Medium | A reachable malicious input corrupts presentation/report content or causes material bounded browser/developer disruption. | Self-only sample errors and unsupported full-application embeddings do not establish a shared-service vulnerability. |
| Low | Limited reversible artifact-integrity failure without credential access or important downstream effects. | Broken slides, intentional typing errors, and ordinary authorized edits are quality issues. |

Architecture confidence is limited to inspected source and the pinned inventory. Live permission settings, external services and actual downstream adoption were not tested. Architecture mapping is not completed security-audit coverage. Material claims were reconciled before publication.

Repository: github.com/mathspace/python-types-workshop
Version: e32a96611c83644184eb3e4855dafb924df20362
