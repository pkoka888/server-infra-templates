# Phase 2 Attribution Modeling Roadmap

## Overview

This roadmap outlines the implementation plan for multi-touch attribution modeling in the marketing analytics platform. Phase 2 builds on the foundational pipeline established in Phase 1.

## Milestones

### Milestone 1: Foundation (Weeks 1-2)
**Target Date**: 2026-04-22

**Objectives**:
- Set up attribution infrastructure
- Implement user stitching for cross-device tracking
- Create journey reconstruction pipeline

**Deliverables**:
- `int_customer_journeys` ephemeral model
- `int_customer_touchpoints` intermediate model
- User stitching logic with device graph
- Documentation and tests

**Success Criteria**:
- 90%+ user identification rate
- Journey reconstruction for 95%+ of orders
- <2 hour processing time for daily refresh

**Resources**:
- 1 Data Engineer (full-time)
- 0.5 Analytics Engineer (part-time)

---

### Milestone 2: First/Last Touch Attribution (Weeks 3-4)
**Target Date**: 2026-05-06

**Objectives**:
- Implement first-touch and last-touch attribution models
- Create attribution mart models
- Build comparison reporting

**Deliverables**:
- `attribution_first_touch` mart model
- `attribution_last_touch` mart model
- `fct_attributed_revenue` aggregated model
- Comparison dashboard in Metabase

**Success Criteria**:
- Attribution totals reconcile within 2% of actual revenue
- Dashboard displays attribution by channel
- dbt tests pass with 100% success rate

**Resources**:
- 1 Data Engineer (full-time)
- 0.5 Analytics Engineer (part-time)

---

### Milestone 3: Linear & Time-Decay Attribution (Weeks 5-6)
**Target Date**: 2026-05-20

**Objectives**:
- Implement linear attribution
- Implement time-decay attribution with configurable decay
- Add attribution model selection to dashboards

**Deliverables**:
- `attribution_linear` mart model
- `attribution_time_decay` mart model
- Configurable decay factor parameter
- Updated Metabase dashboard with model selector

**Success Criteria**:
- All attribution models produce consistent totals
- Decay factor can be adjusted via dbt variable
- Dashboard allows model comparison

**Resources**:
- 1 Data Engineer (full-time)
- 0.5 Analytics Engineer (part-time)

---

### Milestone 4: Position-Based Attribution (Weeks 7-8)
**Target Date**: 2026-06-03

**Objectives**:
- Implement U-shaped (position-based) attribution
- Make weights configurable per client
- Build executive reporting views

**Deliverables**:
- `attribution_position_based` mart model
- Client-specific weight configuration
- Executive summary dashboards
- Automated attribution reporting

**Success Criteria**:
- Position weights configurable via dbt project vars
- Executive dashboard shows attribution summary
- Automated daily reports generated

**Resources**:
- 1 Data Engineer (full-time)
- 0.5 Analytics Engineer (part-time)
- 0.25 Product Manager (part-time)

---

### Milestone 5: Validation & Rollout (Weeks 9-10)
**Target Date**: 2026-06-17

**Objectives**:
- Validate attribution accuracy
- Pilot with 2 clients
- Train stakeholders
- Document usage

**Deliverables**:
- Validation report comparing models
- Client pilot results
- Training documentation
- User guides

**Success Criteria**:
- Client sign-off on attribution methodology
- Attribution variance <2% for pilot clients
- Stakeholder training completed

**Resources**:
- 1 Data Engineer (full-time)
- 0.5 Analytics Engineer (part-time)
- 1 Product Manager (part-time)

---

### Milestone 6: Data-Driven Attribution (Weeks 11-16)
**Target Date**: 2026-07-29

**Objectives**:
- Research ML-based attribution approaches
- Implement Markov chain attribution
- Build model training pipeline

**Deliverables**:
- Research report on ML attribution options
- Markov chain attribution prototype
- Model training pipeline
- Evaluation framework

**Success Criteria**:
- ML model produces actionable insights
- Model accuracy >80% on validation set
- Pipeline runs automatically daily

**Resources**:
- 1 Data Scientist (full-time)
- 1 Data Engineer (0.5 time)
- 1 ML Engineer (part-time)

---

### Milestone 7: Production ML Attribution (Weeks 17-20)
**Target Date**: 2026-08-26

**Objectives**:
- Productionize ML attribution model
- A/B test against rule-based models
- Build model monitoring

**Deliverables**:
- Production ML attribution model
- A/B test results
- Model monitoring dashboard
- Retraining pipeline

**Success Criteria**:
- ML model outperforms rule-based models in A/B test
- Model drift detection in place
- <1% model failure rate

**Resources**:
- 1 Data Scientist (full-time)
- 1 Data Engineer (0.5 time)
- 1 ML Engineer (0.5 time)

---

## Resource Requirements Summary

| Role | Phase 2A (Wks 1-10) | Phase 2B (Wks 11-20) | Total Effort |
|------|---------------------|----------------------|--------------|
| Data Engineer | 1.0 FTE | 0.5 FTE | 15 weeks |
| Analytics Engineer | 0.5 FTE | 0.0 FTE | 5 weeks |
| Data Scientist | 0.0 FTE | 1.0 FTE | 10 weeks |
| ML Engineer | 0.0 FTE | 0.5 FTE | 5 weeks |
| Product Manager | 0.25 FTE | 0.0 FTE | 2.5 weeks |

**Total Effort**: ~37.5 person-weeks

---

## Risk Assessment

### High Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient user identification | High | Implement device graph, use probabilistic matching |
| Data quality issues | High | Add data validation, implement quality checks |
| Client resistance to methodology | Medium | Involve clients early, provide multiple models |

### Medium Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance degradation | Medium | Optimize queries, add materializations |
| Model accuracy below threshold | Medium | Fall back to rule-based, iterate on ML |

### Low Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Delayed timeline | Low | Prioritize core features, use agile sprints |

---

## Success Criteria

### Technical Success
- [ ] All attribution models reconcile within 2% of actual revenue
- [ ] 95%+ of orders have complete journey data
- [ ] Attribution pipeline completes within SLA (4 hours)
- [ ] 99.9% uptime for attribution services

### Business Success
- [ ] 2+ clients actively using attribution reports
- [ ] Attribution insights drive 10%+ budget reallocation
- [ ] ROAS improvement of 15%+ for optimized campaigns

### User Success
- [ ] Dashboard adoption rate >80% for target users
- [ ] User satisfaction score >4.0/5.0
- [ ] <5 support tickets per week related to attribution

---

## Dependencies

### External Dependencies
- GA4 BigQuery export access
- Facebook Marketing API permissions
- Client UTM tagging compliance

### Internal Dependencies
- Phase 1 pipeline completion
- dbt models for staging data
- Metabase dashboard infrastructure

---

## Budget Estimate

| Category | Phase 2A (Wks 1-10) | Phase 2B (Wks 11-20) | Total |
|----------|---------------------|----------------------|-------|
| Engineering | $75,000 | $100,000 | $175,000 |
| Infrastructure | $2,000 | $5,000 | $7,000 |
| Tools & Licenses | $1,000 | $3,000 | $4,000 |
| Training | $2,000 | $2,000 | $4,000 |
| **Total** | **$80,000** | **$110,000** | **$190,000** |

---

## Timeline Summary

```
Week:  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20
       |--M1--|--M2--|--M3--|--M4--|--M5--|------M6------|--M7--|
       
M1: Foundation
M2: First/Last Touch
M3: Linear & Time-Decay
M4: Position-Based
M5: Validation & Rollout
M6: Data-Driven Research
M7: Production ML Attribution
```

---

## Next Steps

1. **Immediate (This Week)**:
   - Finalize resource allocation
   - Set up attribution development environment
   - Create detailed technical specs for Milestone 1

2. **Short-term (Next 2 Weeks)**:
   - Begin Milestone 1 implementation
   - Establish weekly check-ins with stakeholders
   - Set up attribution testing framework

3. **Medium-term (Month 1)**:
   - Complete Milestones 1-2
   - Pilot with 1 client
   - Gather early feedback
