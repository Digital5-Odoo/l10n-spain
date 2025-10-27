-- set test environment
UPDATE res_company
SET tbai_test_enabled = True
WHERE tbai_enabled = True;
