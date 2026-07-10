# Production Deployment Checklist

**Version:** 1.0.0  
**Date:** 2026-07-10  
**Status:** Pre-Deployment

---

## Overview

This checklist ensures safe, auditable deployment of database migrations and severity corrections to production.

**Critical Requirements:**
- Database backup before any changes
- Staging environment validation
- Migration verification
- Rollback capability tested
- Post-deployment health checks

---

## Pre-Deployment

### 1. Environment Preparation

- [ ] **Staging Environment Ready**
  - [ ] Staging database contains production copy
  - [ ] Staging isolated from production
  - [ ] Staging credentials configured

- [ ] **Backup Production Database**
  ```bash
  # Via Supabase Dashboard:
  # Project → Database → Backups → Create backup
  
  # Or via pg_dump:
  pg_dump -h <host> -U postgres -d postgres -F c -f backup_pre_deployment_$(date +%Y%m%d).dump
  ```
  - [ ] Backup file size verified
  - [ ] Backup stored in safe location
  - [ ] Restoration tested (staging only)

- [ ] **Rollback Scripts Ready**
  - [ ] `rollback_severity_corrections.py` tested in staging
  - [ ] Rollback procedure documented
  - [ ] Rollback tested successfully in staging

---

## Staging Deployment

### 2. Apply Migrations to Staging

- [ ] **Migration 000: Migrations Table**
  ```sql
  -- Copy from: migrations/000_create_migrations_table.sql
  -- Execute in Supabase SQL Editor (Staging)
  ```
  - [ ] Executed successfully
  - [ ] `schema_migrations` table created
  - [ ] Initial record inserted

- [ ] **Migration 001: Enrichment Status**
  ```sql
  -- Copy from: migrations/001_add_enrichment_status.sql
  -- Execute in Supabase SQL Editor (Staging)
  ```
  - [ ] Executed successfully
  - [ ] `enrichment_status` column added
  - [ ] Index created
  - [ ] Existing records initialized to 'raw_database'

- [ ] **Migration 002: Provenance Metadata**
  ```sql
  -- Copy from: migrations/002_add_provenance_metadata.sql
  -- Execute in Supabase SQL Editor (Staging)
  ```
  - [ ] Executed successfully
  - [ ] `severity_explanation` column added
  - [ ] JSONB metadata columns added
  - [ ] GIN indexes created

- [ ] **Migration 003: Audit Log**
  ```sql
  -- Copy from: migrations/003_create_audit_log.sql
  -- Execute in Supabase SQL Editor (Staging)
  ```
  - [ ] Executed successfully
  - [ ] `enrichment_audit_log` table created
  - [ ] Indexes created
  - [ ] Trigger function created
  - [ ] Trigger attached to obd_codes table

### 3. Verify Migrations (Staging)

Run migration verification script:

```bash
python verify_migrations.py --env staging
```

- [ ] **Schema Verification**
  - [ ] All expected columns exist
  - [ ] All expected indexes exist
  - [ ] All expected tables exist
  - [ ] Data types correct

- [ ] **Data Integrity**
  - [ ] Existing records unchanged (except enrichment_status default)
  - [ ] No NULL values in required fields
  - [ ] JSON columns accept valid JSON
  - [ ] Foreign key constraints working

- [ ] **Functionality Tests**
  - [ ] Can insert new records
  - [ ] Can update existing records
  - [ ] Can query with new columns
  - [ ] Audit trigger fires on updates
  - [ ] Indexes improve query performance

### 4. Apply Severity Corrections (Staging)

```bash
python apply_confidence_severity.py --yes --env staging
```

- [ ] **Corrections Applied**
  - [ ] High confidence corrections applied
  - [ ] Medium confidence review queue generated
  - [ ] Low confidence codes left unchanged
  - [ ] Audit log entries created

- [ ] **Verification**
  - [ ] P0450 severity changed: High → Moderate
  - [ ] P0450 severity_explanation populated
  - [ ] Sample 20 random codes reviewed manually
  - [ ] No unintended changes
  - [ ] Audit log complete

- [ ] **Review Queue Processed**
  - [ ] Medium confidence corrections reviewed
  - [ ] Approved corrections applied
  - [ ] Rejected corrections documented

### 5. Staging Validation

- [ ] **Random Sample Testing (50 codes)**
  - [ ] Severity ratings appropriate
  - [ ] Severity explanations accurate
  - [ ] No data corruption
  - [ ] Existing data preserved

- [ ] **Query Performance**
  - [ ] Index performance verified
  - [ ] No query regressions
  - [ ] JSONB queries performant

- [ ] **Rollback Test**
  ```bash
  python rollback_severity_corrections.py --codes P0450,P0442 --execute --env staging
  ```
  - [ ] Rollback successful
  - [ ] Original values restored
  - [ ] Audit log updated
  - [ ] Re-apply corrections after test

### 6. Staging Sign-Off

- [ ] All tests passed
- [ ] No critical issues found
- [ ] Team approval obtained
- [ ] Production deployment scheduled

---

## Production Deployment

### 7. Pre-Deployment Checks

- [ ] **Maintenance Window Scheduled**
  - Start time: ______________
  - End time: ______________
  - Stakeholders notified: [ ]

- [ ] **Database State Verified**
  - [ ] Current backup is recent (<24 hours)
  - [ ] No ongoing critical operations
  - [ ] Connection pool stable

- [ ] **Team Availability**
  - [ ] Database admin available
  - [ ] Developer on call
  - [ ] Rollback authority identified

### 8. Apply Migrations to Production

Execute each migration in sequence via Supabase SQL Editor:

- [ ] **Migration 000** (Migrations Table)
  - Execution time: ______________
  - Status: [ ] Success [ ] Failed
  - Notes: ______________

- [ ] **Migration 001** (Enrichment Status)
  - Execution time: ______________
  - Status: [ ] Success [ ] Failed
  - Notes: ______________

- [ ] **Migration 002** (Provenance Metadata)
  - Execution time: ______________
  - Status: [ ] Success [ ] Failed
  - Notes: ______________

- [ ] **Migration 003** (Audit Log)
  - Execution time: ______________
  - Status: [ ] Success [ ] Failed
  - Notes: ______________

**If any migration fails:**
1. STOP immediately
2. Document error
3. Restore from backup
4. Debug in staging
5. Do NOT proceed with corrections

### 9. Verify Production Migrations

```bash
python verify_migrations.py --env production
```

- [ ] All schema changes verified
- [ ] Data integrity confirmed
- [ ] Functionality tests passed

**If verification fails:**
1. STOP immediately
2. Do NOT apply corrections
3. Restore from backup

### 10. Apply Severity Corrections to Production

```bash
python apply_confidence_severity.py --yes --env production
```

- [ ] High confidence corrections applied
- [ ] Review queue generated
- [ ] Audit log populated
- [ ] No errors reported

**Correction Statistics:**
- High confidence applied: ______________
- Medium confidence queued: ______________
- Low confidence unchanged: ______________

### 11. Post-Deployment Verification

- [ ] **Health Checks**
  - [ ] API responding normally
  - [ ] Database connections stable
  - [ ] Query performance normal
  - [ ] No error spike in logs

- [ ] **Sample Validation (20 codes)**
  - [ ] P0450: Severity = Moderate, explanation present
  - [ ] P0442: Severity = Moderate, explanation present
  - [ ] P0420: Severity = Moderate, explanation present
  - [ ] Sample O2 codes: Severity = Moderate
  - [ ] Sample misfire codes: Severity = High
  - [ ] All have severity_explanation populated

- [ ] **Audit Log Check**
  ```sql
  SELECT COUNT(*) FROM enrichment_audit_log WHERE action = 'severity_updated';
  -- Should match number of corrections applied
  ```
  - [ ] Audit entries count correct
  - [ ] All corrections logged
  - [ ] Structured events valid

- [ ] **User-Facing Validation**
  - [ ] Request P0450 via API
  - [ ] Verify correct severity displayed
  - [ ] Verify severity explanation shown
  - [ ] Verify formatting correct

### 12. Monitor for Issues

**First Hour:**
- [ ] Monitor error logs every 15 minutes
- [ ] Check query performance
- [ ] Watch for user issues

**First 24 Hours:**
- [ ] Monitor error rate trends
- [ ] Review user feedback
- [ ] Check for data anomalies

---

## Rollback Procedure

### If Issues Detected

**Immediate Actions:**
1. Assess severity of issue
2. Determine if rollback needed
3. Notify team

**Rollback Steps:**

1. **Rollback Severity Corrections**
   ```bash
   python rollback_severity_corrections.py --execute --env production
   ```
   - [ ] Corrections rolled back
   - [ ] Verification: Sample codes restored
   - [ ] Audit log updated

2. **Rollback Migrations** (if schema issues)
   ```bash
   # Restore from pre-deployment backup
   pg_restore -h <host> -U postgres -d postgres backup_pre_deployment_YYYYMMDD.dump
   ```
   - [ ] Database restored
   - [ ] Data integrity verified
   - [ ] Application functioning

3. **Post-Rollback Verification**
   - [ ] System stable
   - [ ] No data loss
   - [ ] Users unaffected
   - [ ] Issue documented

---

## Post-Deployment

### 13. Documentation

- [ ] **Deployment Record**
  - [ ] Migrations applied documented
  - [ ] Correction statistics recorded
  - [ ] Issues encountered noted
  - [ ] Resolution steps documented

- [ ] **Audit Trail**
  - [ ] All changes logged in audit system
  - [ ] Backup location recorded
  - [ ] Rollback procedures validated

- [ ] **Knowledge Base Update**
  - [ ] P0450 now returns correct information
  - [ ] 457 codes have updated severity
  - [ ] Severity explanations added

### 14. Team Communication

- [ ] Deployment complete notification sent
- [ ] Summary statistics shared
- [ ] Known issues communicated
- [ ] Next steps outlined

---

## Success Criteria

Deployment is considered successful when:

- ✅ All migrations applied successfully
- ✅ All verification checks passed
- ✅ High confidence corrections applied (457 codes)
- ✅ P0450 severity corrected: High → Moderate
- ✅ Severity explanations added to all corrected codes
- ✅ Audit log complete and accurate
- ✅ No production incidents
- ✅ Rollback capability verified
- ✅ User-facing functionality improved

---

## Rollback Criteria

Initiate rollback if:

- ❌ Migration fails to execute
- ❌ Data corruption detected
- ❌ Critical functionality broken
- ❌ Significant error rate increase
- ❌ Performance degradation >20%
- ❌ User-facing issues reported

---

## Timeline

**Estimated Duration:**
- Migrations: 10-15 minutes
- Verification: 15-20 minutes
- Corrections: 10-15 minutes
- Validation: 20-30 minutes
- **Total: 55-80 minutes**

**Recommended Window:** 2 hours (includes buffer)

---

## Approval

### Pre-Deployment Approval

- [ ] Staging validation complete
- [ ] Rollback tested successfully
- [ ] Backup verified
- [ ] Team briefed

**Approved by:** ______________  
**Date:** ______________

### Post-Deployment Sign-Off

- [ ] All success criteria met
- [ ] No critical issues
- [ ] Documentation complete
- [ ] Ready for Phase 2 (enrichment)

**Signed off by:** ______________  
**Date:** ______________

---

## Phase 2 Preparation

After successful deployment:

- [ ] Review medium confidence queue (8 codes)
- [ ] Apply approved medium confidence corrections
- [ ] Begin Tier 1 enrichment planning
- [ ] Schedule enrichment Phase 2

---

## Contact Information

**Database Admin:** ______________  
**On-Call Developer:** ______________  
**Project Lead:** ______________  
**Emergency Contact:** ______________

---

## Appendix: Command Reference

```bash
# Backup database
pg_dump -h <host> -U postgres -d postgres -F c -f backup.dump

# Verify migrations
python verify_migrations.py --env production

# Apply severity corrections
python apply_confidence_severity.py --yes --env production

# Rollback corrections
python rollback_severity_corrections.py --execute --env production

# Restore database
pg_restore -h <host> -U postgres -d postgres backup.dump
```

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-07-10  
**Next Review:** After Phase 1 deployment
