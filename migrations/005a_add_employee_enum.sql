-- Migration 005a: Add employee value to role enum
-- This migration adds the 'employee' value to the roleenum_v2 enum

ALTER TYPE roleenum_v2 ADD VALUE 'employee';