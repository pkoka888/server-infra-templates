Yes — the plan is solid, but it is also a bit too “complete on paper” and could benefit from a stricter implementation strategy that prioritizes standards, reusable patterns, and connector-first discovery before expanding scope. A better approach is to force an early “research and reduce” phase, then execute in isolated worktrees with subagents so each part stays small, testable, and easy to extend later. [stellans](https://stellans.io/dbt-project-structure-conventions/)

## What to change in the plan

The biggest improvement is to shift from “build everything” to “pick the smallest standard path that can survive growth.” dbt project conventions are much easier to maintain when you keep the layered structure clean and consistent, instead of inventing custom patterns for every source or use case. For orchestration, Prefect in Docker is a good fit, but the design should emphasize isolated workers, health checks, and deployment-based execution rather than a loose collection of scripts. [oneuptime](https://oneuptime.com/blog/post/2026-02-08-how-to-run-prefect-in-docker-for-data-pipeline-orchestration/view)

## Research first, then build

Before implementing, make the agent research the most common failure modes for the exact stack and sources: GA4, Facebook Ads, PrestaShop, Airbyte connector limits, API scopes, sync latency, schema drift, and attribution mismatches. Facebook connectors are especially prone to API-specific quirks, like response-size limits or scope-related issues, so connector research should happen before modeling or dashboard work. Great Expectations and dbt tests should be selected from the most likely real-world failures first, not from an abstract “full coverage” checklist. [cevo.com](https://cevo.com.au/post/prioritising-data-quality-with-dbt-expectations-a-practical-approach-to-building-reliable-data-pipelines/)

## Avoid reinventing

Prefer established patterns already used by the tools and ecosystem: staged dbt layers, service isolation in Docker Compose, vendor-neutral lineage with OpenLineage, and standard orchestration patterns in Prefect. If a connector, workflow, or skill already exists, reuse it instead of designing a new one; the goal is to assemble a reliable system, not create custom infrastructure where a standard module already exists. The MCP principle here is simple: fewer tools, better named, more outcome-focused, and only as many as the agent actually needs. [openlineage](https://openlineage.io/docs/integrations/dbt/)

## Suggested execution model

Use a **worktree-per-task** approach for parallel agent work, because it isolates changes without turning the repo into a conflict zone. A practical split would be: [youtube](https://www.youtube.com/watch?v=m2QbDiJuemI)

- One subagent researches connectors and source constraints.
- One subagent defines Docker Compose and environment isolation.
- One subagent validates dbt structure, naming, and testing standards.
- One subagent designs orchestration and failure handling.
- One subagent reviews “common problems” and produces an anti-overthinking checklist.

That gives you parallelism without letting the agent merge architecture decisions too early. [docs.agentinterviews](https://docs.agentinterviews.com/blog/parallel-ai-coding-with-gitworktrees/)

## Prioritized implementation order

Start with the boring but high-value foundations:

1. Confirm the **common connector problems** for each source.
2. Validate whether the stack fits cleanly in Docker Compose first.
3. Decide the minimal warehouse schema and dbt layer standards.
4. Define orchestration only after source sync and modeling boundaries are clear.
5. Add lineage, quality, and dashboards after the ingestion-to-mart path works once.

That order reduces overthinking because it forces the agent to answer “what breaks first?” before asking “what can we add later?”. [docs.airbyte](https://docs.airbyte.com/integrations/sources/facebook-pages)

## Example instruction block for the agent

You can give the agent a directive like this:

- Research first: list the top 5 failure modes for each source connector.
- Reuse standards: prefer existing Airbyte/dbt/Prefect/OpenLineage patterns over custom design.
- Keep the architecture Docker-first: every component must run cleanly in Compose before anything else.
- Use worktrees for parallel tasks: one worktree per subtask, merged only after review.
- Define small interfaces: source → raw → staging → marts → BI, nothing extra.
- Prefer existing MCP servers, skills, and workflows before creating new ones.
- Stop expanding scope when the path to phase 1 is already sufficient.
- Document extension points, but do not implement future phases early.

## A better planning prompt

Here is a cleaner planning prompt you can reuse:

“Before implementation, research the most common connector, orchestration, dbt, and Docker problems for GA4, Facebook Ads, and PrestaShop. Then propose the smallest standards-based architecture that uses existing tools, existing workflows, and existing MCP/skills where possible. Prefer Docker Compose for the first deployable version. Split implementation into parallel worktrees with subagents, one topic per worktree, and avoid inventing custom abstractions unless a standard pattern does not exist. Focus on phase 1 only, define extension points for phase 2+, and include explicit anti-overthinking rules.”

If you want, I can turn your current plan into a sharper agent execution checklist with:

- research tasks,
- worktree/subagent split,
- Docker-first deployment order,
- and a “do not overengineer” guardrail list.

Below is a sharper execution checklist you can hand to the agent. It is structured to force research-first decisions, split work cleanly across parallel worktrees, keep the deployment Docker-first, and prevent scope creep. The recommendations are aligned with current MCP/server design guidance, dbt structure conventions, Prefect Docker deployment guidance, and common data-pipeline integration patterns. [zenml](https://www.zenml.io/llmops-database/best-practices-for-building-production-grade-mcp-servers-for-ai-agents)

## 1) Research tasks

1. Identify the top connector risks for each source: GA4, Facebook Ads, PrestaShop.
2. Confirm the actual Airbyte connector availability, sync limits, and auth requirements for each source.
3. Check common failure modes: schema drift, API throttling, incremental sync gaps, timezone issues, duplicate events, and attribution mismatches.
4. Verify the standard dbt project layout and naming conventions before creating any models.
5. Verify Prefect deployment patterns for Docker-based workers, task execution, retries, and observability.
6. Review Great Expectations and dbt tests to decide which checks belong where.
7. Confirm OpenLineage integration points so lineage is added once, not retrofitted later.
8. Research existing examples for Docker Compose isolation, secrets handling, and service health checks.
9. Research whether any existing MCP servers, skills, or workflows already solve parts of the implementation.
10. Produce a “common problems first” memo before writing production code.

## 2) Worktree split

Create one worktree per concern so subagents can work in parallel without merging architecture too early. This reduces conflicts and prevents one agent from expanding scope into another agent’s domain. [youtube](https://www.youtube.com/watch?v=m2QbDiJuemI)

### Recommended split

- `wt-research-connectors`
- `wt-docker-stack`
- `wt-dbt-standards`
- `wt-orchestration-prefect`
- `wt-quality-lineage`
- `wt-review-integration`

### Subagent roles

- Researcher: connector constraints, API quirks, common failures.
- Platform engineer: Docker Compose, networking, volumes, secrets, health checks.
- Analytics engineer: dbt structure, staging/marts conventions, tests.
- Orchestration engineer: Prefect flows, retries, scheduling, deployment.
- Quality engineer: Great Expectations + dbt test split, validation policy.
- Reviewer: integration consistency, standards compliance, overengineering check.

## 3) Docker-first order

Build the system in the smallest runnable slices. Prefect, Airbyte, dbt, and Metabase all have sensible Docker-oriented deployment patterns, so the first goal is not “full analytics platform,” but “one stable local stack that syncs, transforms, and shows one dashboard”. [airbyte](https://airbyte.com/etl-tools/airbyte-vs-prefect)

### Order of execution

1. Define a minimal `docker-compose.yml` with Postgres, Airbyte, Prefect, Metabase.
2. Add health checks, persistent volumes, and a shared network.
3. Add secrets via `.env` or a secrets store, not inline values.
4. Bring up the warehouse first and confirm connectivity.
5. Bring up Airbyte and validate one source sync end-to-end.
6. Add dbt project skeleton and one staging model.
7. Add Prefect flow to orchestrate sync → dbt run → dbt test.
8. Add Great Expectations only for gaps not already covered by dbt tests.
9. Add Metabase with one dashboard on top of a gold model.
10. Only then expand to attribution, cohorts, automation, and extra sources.

## 4) Implementation checklist

### Foundation

- [ ] Use one warehouse.
- [ ] Use one canonical schema naming convention.
- [ ] Use one dbt layer pattern: `staging`, `intermediate`, `marts`.
- [ ] Use one orchestration entrypoint.
- [ ] Use one dashboard path for the first release.

### Ingestion

- [ ] Validate connectors before modeling.
- [ ] Document auth method, sync frequency, watermark behavior, and known limits for each source.
- [ ] Define raw schema-per-source naming.
- [ ] Store raw loads before transformation.

### Transformation

- [ ] Keep staging models thin and mechanical.
- [ ] Put business logic in intermediate or marts, not staging.
- [ ] Add tests for uniqueness, not null, accepted values, and relationships.
- [ ] Keep incremental logic only where scale requires it.

### Orchestration

- [ ] Run source syncs explicitly.
- [ ] Run dbt after sync completion.
- [ ] Run tests after transforms.
- [ ] Fail fast on quality errors.
- [ ] Emit logs and run metadata for every step.

### Quality and lineage

- [ ] Use dbt tests for structural guarantees.
- [ ] Use Great Expectations for data-volume and anomaly checks.
- [ ] Add lineage from dbt and orchestration once the path is stable.
- [ ] Document the exact conditions that trigger alerts.

## 5) Anti-overengineering rules

1. Do not build phase 2 features during phase 1.
2. Do not create custom abstractions when a tool convention already exists.
3. Do not add another service unless it solves a concrete failure mode.
4. Do not design generic frameworks for one concrete pipeline.
5. Do not split a model into multiple layers unless the logic truly differs.
6. Do not add lineage, alerting, or automation before the core sync-transform path works.
7. Do not create custom MCP tools if a standard tool already covers the task.
8. Do not make dashboards before the mart schema is stable.
9. Do not optimize for imaginary scale; optimize for the first real production workload.
10. Do not merge unrelated concerns into one subagent task.

## 6) Agent instruction template

Use this as the agent’s operational brief:

“Research the most common implementation problems first. Prefer existing standards, existing tools, and existing workflows over custom design. Split the work into parallel worktrees by concern. Build Docker-first and verify each layer before adding the next. Keep phase 1 minimal: one ingestion path, one dbt path, one orchestration path, one dashboard path. Add only extension points that are needed for the next concrete use case. Reject any idea that increases complexity without reducing a known risk.”

## 7) What the plan should output

The agent should produce these artifacts:

- Research memo for common connector and orchestration problems.
- Docker Compose blueprint.
- dbt project convention guide.
- Prefect flow outline.
- Data quality policy.
- Lineage integration note.
- Phase 1 implementation order.
- Explicit list of deferred phase 2+ items.

The strongest improvement here is discipline: research first, standards second, implementation third. [snyk](https://snyk.io/articles/5-best-practices-for-building-mcp-servers/)

Here is a practical package you can drop into the agent plan. It covers a dbt project checklist, a Prefect Docker work pool pattern, dbt-expectations examples, integration guidance for Airbyte/Superset/Metabase, subagent flow templates, MCP overengineering pitfalls, and how to fold FastMCP into the checklist without overbuilding. [docs.prefect](https://docs.prefect.io/v3/how-to-guides/deployment_infra/docker)

## dbt project checklist

- Keep raw sources isolated and reference them only through `source()` in staging models.
- Use the standard layers: `staging`, `intermediate`, `marts`.
- Make staging models thin: rename, recast, and standardize fields only.
- Put business logic in marts or intermediate models, not in staging.
- Add tests in `schema.yml` beside models, not scattered across ad hoc SQL.
- Use `ref()` everywhere possible instead of hardcoding table names.
- Prefer incremental models only when volume justifies it.
- Document sources, models, and metrics early.
- Add one style guide for naming, null handling, and timestamps.
- Keep one package policy: only install packages that solve an active requirement. [thedataschool.co](https://www.thedataschool.co.uk/curtis-paterson/organising-a-dbt-project-best-practices/)

### Example `dbt_project.yml`

```yaml
name: marketing_analytics
version: 1.0.0
config-version: 2

profile: marketing_analytics

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]
clean-targets: ["target", "dbt_packages"]

models:
  marketing_analytics:
    +materialized: view
    staging:
      +materialized: view
      +schema: staging
      +tags: ["staging"]
    intermediate:
      +materialized: view
      +schema: intermediate
      +tags: ["intermediate"]
    marts:
      +materialized: table
      +schema: marts
      +tags: ["marts"]
      core:
        +materialized: table
      marketing:
        +materialized: table

seeds:
  marketing_analytics:
    +schema: seeds
    +quote_columns: false

vars:
  timezone: "Europe/Prague"
  freshness_hours: 24
```

## Prefect Docker work pool

Prefect’s Docker work pool pattern is the right fit for agentic orchestration because it separates deployment metadata from execution containers and uses a worker that polls the pool. For this project, the agent should treat Airbyte syncs, dbt runs, and validation tasks as Docker-run jobs rather than inline shell hacks. [docs.prefect](https://docs.prefect.io/v3/concepts/work-pools)

### Setup steps

1. Start Prefect server.
2. Create a Docker work pool.
3. Start a Docker worker attached to that pool.
4. Define a deployment for the Airbyte-orchestration flow.
5. Use a shared Docker network so Prefect can reach Airbyte, Postgres, and dbt runtime containers.
6. Mount only the files needed for the flow.
7. Keep credentials in environment variables or Prefect blocks.

### Template commands

```bash
prefect server start
prefect work-pool create airbyte-docker-pool --type docker
prefect worker start --pool airbyte-docker-pool
```

### Flow pattern

```python
from prefect import flow, task

@task
def sync_airbyte(connection_id: str):
    ...

@task
def run_dbt():
    ...

@task
def run_tests():
    ...

@flow(name="airbyte_dbt_pipeline")
def pipeline():
    sync_airbyte("ga4")
    sync_airbyte("facebook")
    sync_airbyte("prestashop")
    run_dbt()
    run_tests()
```

## dbt-expectations examples

Use dbt-expectations for tests that are more expressive than core dbt constraints, especially regex, distribution, range, and anomaly-style checks. Keep the core structural tests in plain dbt and use dbt-expectations for higher-signal checks. [cevo.com](https://cevo.com.au/post/prioritising-data-quality-with-dbt-expectations-a-practical-approach-to-building-reliable-data-pipelines/)

### Example `schema.yml`

```yaml
version: 2

models:
  - name: fct_orders
    columns:
      - name: order_id
        tests:
          - not_null
          - unique

      - name: total_paid_amount
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              strictly: false

      - name: order_status
        tests:
          - dbt_expectations.expect_column_values_to_be_in_set:
              value_set: ["pending", "processing", "completed", "cancelled"]

      - name: customer_email
        tests:
          - dbt_expectations.expect_column_values_to_match_regex:
              regex: '^[^@]+@[^@]+\.[^@]+$'
```

### Useful checks to add first

- Row count not too low or too high.
- Revenue amount never negative.
- Status only from an allowed set.
- Email and identifier pattern validation.
- Duplicate transaction/order detection.
- Distribution checks for spend, orders, and conversion rates. [datadoghq](https://www.datadoghq.com/blog/dbt-data-quality-testing/)

## Airbyte, Superset, Metabase

For this stack, the integration pattern should be: Airbyte lands raw data, dbt transforms it, and BI tools read only from curated marts. Metabase is the simplest first BI tool for business users, while Superset is useful if you need more technical dashboard flexibility later. [getdbt](https://www.getdbt.com/blog/staging-models-best-practices-and-limiting-view-runs)

### Recommended integration model

- Airbyte writes raw tables into Postgres schemas per source.
- dbt builds staging and marts into separate schemas.
- Metabase connects to the marts schema for dashboards.
- Superset can be added later as an advanced visualization layer if needed.
- Do not point BI tools at raw Airbyte schemas unless it is strictly exploratory.

### Practical rollout

1. Connect Airbyte to Postgres.
2. Build one dbt mart: `fct_marketing_performance`.
3. Wire Metabase to the marts schema.
4. Add one executive dashboard.
5. Only add Superset if Metabase limits are actually blocking work.

## Prefect subagent templates

Use subagents as narrow, outcome-driven workers. The strongest pattern is one subagent per question, not one subagent per vague project area. [docs.agentinterviews](https://docs.agentinterviews.com/blog/parallel-ai-coding-with-gitworktrees/)

### Template 1: connector researcher

**Goal:** Identify common failures for GA4, Facebook Ads, PrestaShop.
**Output:** connector risks, auth caveats, sync limits, retry guidance.

### Template 2: dbt standards reviewer

**Goal:** Validate folder layout, naming, materialization, and tests.
**Output:** approved `dbt_project.yml`, schema naming rules, test list.

### Template 3: Docker platform builder

**Goal:** Produce compose stack and network layout.
**Output:** `docker-compose.yml`, service health checks, env layout.

### Template 4: orchestration designer

**Goal:** Define Prefect flow and deployment model.
**Output:** flow template, worker/pool config, retry policy.

### Template 5: quality and lineage reviewer

**Goal:** Decide what belongs in dbt tests vs Great Expectations vs lineage.
**Output:** validation policy and observability checklist.

## MCP overengineering pitfalls

The biggest MCP mistake is building a custom server around a tool that already exists as a reliable standard component. Another common mistake is exposing too many capabilities through one server and turning it into a fragile “everything gateway”. A third mistake is designing tooling before you know the exact agent tasks that need it. [zenml](https://www.zenml.io/llmops-database/best-practices-for-building-production-grade-mcp-servers-for-ai-agents)

### Common pitfalls

- Creating a custom MCP server for every small workflow.
- Exposing too many tools without strict permission boundaries.
- Adding stateful logic where stateless tool calls would work.
- Coupling agent prompts to one specific infrastructure layout.
- Building connectors before defining failure handling.
- Letting the server become the app instead of the integration layer.

## FastMCP integration steps

Use FastMCP only if you need a lightweight MCP server wrapper around clearly bounded tasks; do not use it to justify extra architecture. The clean approach is to expose a minimal set of tools for the agent checklist: research, inspect, validate, and summarize. [philschmid](https://www.philschmid.de/mcp-best-practices)

### Integration steps

1. Define a single purpose for the FastMCP server.
2. Expose only the tools the agent checklist actually needs.
3. Keep tool inputs explicit and small.
4. Separate read-only research tools from mutation tools.
5. Add auth, logging, and request limits from day one.
6. Document the exact tasks the server supports.
7. Avoid duplicating existing CLI or API functionality.

## Guardrail list

- Do not add a new tool unless it removes a proven bottleneck.
- Do not create custom abstractions before the first pipeline run succeeds.
- Do not put business logic in staging.
- Do not let the agent work on phase 2 before phase 1 is healthy.
- Do not build both Metabase and Superset deeply at the same time.
- Do not invent a new orchestration pattern when Prefect’s Docker work pool fits.
- Do not add MCP tools for tasks that can already be done by shell, API, or standard CLI.
- Do not let subagents edit the same area in the same worktree.
- Do not proceed without a common failure-mode memo.
- Do not optimize for future scale before current reliability.

## Minimal agent checklist

1. Research common problems first.
2. Confirm existing connectors and workflows.
3. Set up Docker Compose baseline.
4. Create worktrees and assign subagents.
5. Lock dbt conventions.
6. Add Prefect Docker work pool.
7. Add one Airbyte sync flow.
8. Add one dbt mart and tests.
9. Add one Metabase dashboard.
10. Only then expand scope.

I can turn this into a ready-to-paste `AGENTS.md`, `README.md`, or a step-by-step internal implementation playbook next.
