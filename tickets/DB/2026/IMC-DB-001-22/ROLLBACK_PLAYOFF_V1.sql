-- IMC-DB-001-22 ROLLBACK, NOT EXECUTED.
-- Refresh counts/candidates first. Drop only newly added triggers, then restore only captured 8 rows.
-- IDs/fingerprints/new canonical key guard each update; do not overwrite intervening corrections.
-- Future rows imported after migration have no captured preimage: inventory and review separately; never delete Results.
-- Existing AFTER triggers restore Site payload/hash and report aggregates automatically.
-- TARGET gold
DROP TRIGGER IF EXISTS `trg_GW002_results_playoff_bi`;

DROP TRIGGER IF EXISTS `trg_GW002_results_playoff_bu`;

DROP TRIGGER IF EXISTS `trg_GW003_results_playoff_bi`;

DROP TRIGGER IF EXISTS `trg_GW003_results_playoff_bu`;

DROP TRIGGER IF EXISTS `trg_GW007_results_playoff_bi`;

DROP TRIGGER IF EXISTS `trg_GW007_results_playoff_bu`;

DROP TRIGGER IF EXISTS `trg_GW008_results_playoff_bi`;

DROP TRIGGER IF EXISTS `trg_GW008_results_playoff_bu`;

-- TARGET custom
DROP TRIGGER IF EXISTS `trg_GW001_results_playoff_bi`;

DROP TRIGGER IF EXISTS `trg_GW001_results_playoff_bu`;

DROP TRIGGER IF EXISTS `trg_GW004_results_playoff_bi`;

DROP TRIGGER IF EXISTS `trg_GW004_results_playoff_bu`;

DROP TRIGGER IF EXISTS `trg_GW005_results_playoff_bi`;

DROP TRIGGER IF EXISTS `trg_GW005_results_playoff_bu`;

DROP TRIGGER IF EXISTS `trg_GW006_results_playoff_bi`;

DROP TRIGGER IF EXISTS `trg_GW006_results_playoff_bu`;

DROP TRIGGER IF EXISTS `trg_GW009_results_playoff_bi`;

DROP TRIGGER IF EXISTS `trg_GW009_results_playoff_bu`;

UPDATE `GW001_IMC Results` SET competition_key='GW001|CUS|DOMESTIC|league|4' WHERE sm_fixture_id=368724187 AND fingerprint='bd7dc337bd7dc337bd7dc337bd7dc337bd7dc337bd7dc337bd7dc337bd7dc337' AND competition_key=CONCAT_WS('|',game_world_id,CASE WHEN UPPER(TRIM(COALESCE(sm_country,''))) IN ('','CUS') THEN NULL ELSE UPPER(TRIM(sm_country)) END,'DOMESTIC','playoff',NULLIF(TRIM(sm_division),''));

UPDATE `GW001_IMC Results` SET competition_key='GW001|CUS|DOMESTIC|league|4' WHERE sm_fixture_id=368724188 AND fingerprint='f27550d3f27550d3f27550d3f27550d3f27550d3f27550d3f27550d3f27550d3' AND competition_key=CONCAT_WS('|',game_world_id,CASE WHEN UPPER(TRIM(COALESCE(sm_country,''))) IN ('','CUS') THEN NULL ELSE UPPER(TRIM(sm_country)) END,'DOMESTIC','playoff',NULLIF(TRIM(sm_division),''));

UPDATE `GW001_IMC Results` SET competition_key='GW001|CUS|DOMESTIC|league|4' WHERE sm_fixture_id=368724189 AND fingerprint='e295fc24e295fc24e295fc24e295fc24e295fc24e295fc24e295fc24e295fc24' AND competition_key=CONCAT_WS('|',game_world_id,CASE WHEN UPPER(TRIM(COALESCE(sm_country,''))) IN ('','CUS') THEN NULL ELSE UPPER(TRIM(sm_country)) END,'DOMESTIC','playoff',NULLIF(TRIM(sm_division),''));

UPDATE `GW001_IMC Results` SET competition_key='GW001|CUS|DOMESTIC|league|4' WHERE sm_fixture_id=368724190 AND fingerprint='2035a6492035a6492035a6492035a6492035a6492035a6492035a6492035a649' AND competition_key=CONCAT_WS('|',game_world_id,CASE WHEN UPPER(TRIM(COALESCE(sm_country,''))) IN ('','CUS') THEN NULL ELSE UPPER(TRIM(sm_country)) END,'DOMESTIC','playoff',NULLIF(TRIM(sm_division),''));

UPDATE `GW001_IMC Results` SET competition_key='GW001|CUS|DOMESTIC|league|4' WHERE sm_fixture_id=368724191 AND fingerprint='bca89601bca89601bca89601bca89601bca89601bca89601bca89601bca89601' AND competition_key=CONCAT_WS('|',game_world_id,CASE WHEN UPPER(TRIM(COALESCE(sm_country,''))) IN ('','CUS') THEN NULL ELSE UPPER(TRIM(sm_country)) END,'DOMESTIC','playoff',NULLIF(TRIM(sm_division),''));

UPDATE `GW001_IMC Results` SET competition_key='GW001|CUS|DOMESTIC|league|4' WHERE sm_fixture_id=368724192 AND fingerprint='2fdd96bb2fdd96bb2fdd96bb2fdd96bb2fdd96bb2fdd96bb2fdd96bb2fdd96bb' AND competition_key=CONCAT_WS('|',game_world_id,CASE WHEN UPPER(TRIM(COALESCE(sm_country,''))) IN ('','CUS') THEN NULL ELSE UPPER(TRIM(sm_country)) END,'DOMESTIC','playoff',NULLIF(TRIM(sm_division),''));

UPDATE `GW005_IMC Results` SET competition_key='GW005|CUS|DOMESTIC|league|1' WHERE sm_fixture_id=312788412 AND fingerprint='c99e7e9ac99e7e9ac99e7e9ac99e7e9ac99e7e9ac99e7e9ac99e7e9ac99e7e9a' AND competition_key=CONCAT_WS('|',game_world_id,CASE WHEN UPPER(TRIM(COALESCE(sm_country,''))) IN ('','CUS') THEN NULL ELSE UPPER(TRIM(sm_country)) END,'DOMESTIC','playoff',NULLIF(TRIM(sm_division),''));

UPDATE `GW005_IMC Results` SET competition_key='GW005|CUS|DOMESTIC|league|1' WHERE sm_fixture_id=312788413 AND fingerprint='5301d7fa5301d7fa5301d7fa5301d7fa5301d7fa5301d7fa5301d7fa5301d7fa' AND competition_key=CONCAT_WS('|',game_world_id,CASE WHEN UPPER(TRIM(COALESCE(sm_country,''))) IN ('','CUS') THEN NULL ELSE UPPER(TRIM(sm_country)) END,'DOMESTIC','playoff',NULLIF(TRIM(sm_division),''));
