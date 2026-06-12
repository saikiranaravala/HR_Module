-- 00_reset.sql — empty every seeded table for a clean reload.
-- TRUNCATE bypasses row-level immutability triggers by design (no row events);
-- the append-only platform.audit_event log is deliberately NOT touched.
BEGIN;

TRUNCATE
  migration.sync_conflict, migration.gate_artifact, migration.dq_exception, migration.staged_record,
  succession.discovery_hold, succession.ninebox_placement, succession.talent_profile,
  succession.slate_entry, succession.key_position,
  analytics.org_bridge, analytics.certified_snapshot, analytics.dim_worker,
  service_delivery.access_grant, service_delivery.notification_pref, service_delivery.delegation,
  service_delivery.kb_article, service_delivery.case_note, service_delivery."case",
  learning.certification, learning.completion_record, learning.assignment, learning.content_item,
  performance.feedback, performance.checkin, performance.calibration_adjustment,
  performance.review_doc, performance.review_cycle, performance.goal,
  recruiting.offer, recruiting.application, recruiting.requisition, recruiting.candidate_profile,
  comp.cycle_line, comp.comp_cycle, comp.comp_record, comp.grade_range,
  benefits.enrollment, benefits.benefit_rate, benefits.benefit_plan,
  payroll.pay_result_record, payroll.pay_input_record, payroll.pay_cycle,
  time_labor.accrual_lot, time_labor.time_result, time_labor.time_entry,
  ai.ai_ledger,
  integration.provisioning_action, integration.connector_credential, integration.connector_run,
  workflow.step_execution, workflow.workflow_instance,
  core.assignment, core.position, core.department, core.worker,
  core.work_eligibility, core.national_id, core.person_name, core.person;

COMMIT;
