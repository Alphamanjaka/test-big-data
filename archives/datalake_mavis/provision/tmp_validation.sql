SELECT `_source_table`, COUNT(*) AS nb FROM datalake_silver.patient_fhir GROUP BY `_source_table` ORDER BY nb DESC;
