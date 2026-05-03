-- Migration 005b: Update member roles to employee
-- This migration updates existing 'member' roles to 'employee'

UPDATE users SET role = 'employee' WHERE role = 'member';
UPDATE project_members SET role = 'employee' WHERE role = 'member';