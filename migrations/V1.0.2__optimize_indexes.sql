-- ==============================================================================
-- Migration: V1.0.2__optimize_indexes.sql
-- Description: Add composite indexes for shadowban worker & audit queries
-- Standard: Zero-downtime online DDL (ALGORITHM=INPLACE, LOCK=NONE)
-- ==============================================================================

-- 1. 存活探针高频扫描复合索引 (shadowban_status = 'PENDING' ORDER BY created_at ASC)
ALTER TABLE `audit_logs` 
  ADD INDEX `idx_shadowban_probe` (`shadowban_status`, `created_at`),
  ALGORITHM=INPLACE, LOCK=NONE;

-- 2. 状态筛选分页复合索引 (status = ? ORDER BY created_at DESC)
ALTER TABLE `audit_logs` 
  ADD INDEX `idx_status_created` (`status`, `created_at`),
  ALGORITHM=INPLACE, LOCK=NONE;

-- 3. 账号维度审计复合索引 (account_username = ? ORDER BY created_at DESC)
ALTER TABLE `audit_logs` 
  ADD INDEX `idx_account_created` (`account_username`, `created_at`),
  ALGORITHM=INPLACE, LOCK=NONE;
