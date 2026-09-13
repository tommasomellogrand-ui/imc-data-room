-- NOT EXECUTED. Target custom / Sql1956795_3.
-- Re-inventory before rollback. Remove only these six new triggers, then restore guarded preimages.
-- Existing DB00122 key normalizers remain active. Do not delete/reinsert records.
-- Newly imported records without preimages require a separate reviewed decision; never delete them.
DROP TRIGGER `trg_GW001_results_playoff_div_bi`;

DROP TRIGGER `trg_GW001_mr_playoff_div_bi`;

DROP TRIGGER `trg_GW001_mr_playoff_key_bi`;

DROP TRIGGER `trg_GW001_results_playoff_div_bu`;

DROP TRIGGER `trg_GW001_mr_playoff_div_bu`;

DROP TRIGGER `trg_GW001_mr_playoff_key_bu`;

UPDATE `GW001_IMC Results` SET sm_division='4',competition_key='GW001|DOMESTIC|playoff|4' WHERE game_world_id='GW001' AND sm_fixture_id=368724187 AND fingerprint='bd7dc337bd7dc337bd7dc337bd7dc337bd7dc337bd7dc337bd7dc337bd7dc337' AND sm_division='2' AND competition_key='GW001|DOMESTIC|playoff|2';

UPDATE `GW001_IMC Results` SET sm_division='4',competition_key='GW001|DOMESTIC|playoff|4' WHERE game_world_id='GW001' AND sm_fixture_id=368724188 AND fingerprint='f27550d3f27550d3f27550d3f27550d3f27550d3f27550d3f27550d3f27550d3' AND sm_division='2' AND competition_key='GW001|DOMESTIC|playoff|2';

UPDATE `GW001_IMC Results` SET sm_division='4',competition_key='GW001|DOMESTIC|playoff|4' WHERE game_world_id='GW001' AND sm_fixture_id=368724189 AND fingerprint='e295fc24e295fc24e295fc24e295fc24e295fc24e295fc24e295fc24e295fc24' AND sm_division='3' AND competition_key='GW001|DOMESTIC|playoff|3';

UPDATE `GW001_IMC Results` SET sm_division='4',competition_key='GW001|DOMESTIC|playoff|4' WHERE game_world_id='GW001' AND sm_fixture_id=368724190 AND fingerprint='2035a6492035a6492035a6492035a6492035a6492035a6492035a6492035a649' AND sm_division='3' AND competition_key='GW001|DOMESTIC|playoff|3';

UPDATE `GW001_IMC Results` SET sm_division='4',competition_key='GW001|DOMESTIC|playoff|4' WHERE game_world_id='GW001' AND sm_fixture_id=368724191 AND fingerprint='bca89601bca89601bca89601bca89601bca89601bca89601bca89601bca89601' AND sm_division='4' AND competition_key='GW001|DOMESTIC|playoff|4';

UPDATE `GW001_IMC Results` SET sm_division='4',competition_key='GW001|DOMESTIC|playoff|4' WHERE game_world_id='GW001' AND sm_fixture_id=368724192 AND fingerprint='2fdd96bb2fdd96bb2fdd96bb2fdd96bb2fdd96bb2fdd96bb2fdd96bb2fdd96bb' AND sm_division='4' AND competition_key='GW001|DOMESTIC|playoff|4';

UPDATE `GW001_IMC Match Report` SET sm_division='4',competition_key='GW001|CUS|DOMESTIC|league|4' WHERE game_world_id='GW001' AND sm_fixture_id=368724187 AND fingerprint='bc1e6a2344986c197d05b1fc6485d55be04364d330f711928a1360c7920fee4a' AND sm_division='2' AND competition_key='GW001|DOMESTIC|playoff|2';

UPDATE `GW001_IMC Match Report` SET sm_division='4',competition_key='GW001|CUS|DOMESTIC|league|4' WHERE game_world_id='GW001' AND sm_fixture_id=368724188 AND fingerprint='e79b1ffba4e87494d0d4d2a2d1be81868a9c6c5a5011d8da1e877c751d4575fd' AND sm_division='2' AND competition_key='GW001|DOMESTIC|playoff|2';

UPDATE `GW001_IMC Match Report` SET sm_division='4',competition_key='GW001|CUS|DOMESTIC|league|4' WHERE game_world_id='GW001' AND sm_fixture_id=368724189 AND fingerprint='e04c26754183f96fb60ef3ed8eadc96d10acce719736193673bc0f2a4a542aea' AND sm_division='3' AND competition_key='GW001|DOMESTIC|playoff|3';

UPDATE `GW001_IMC Match Report` SET sm_division='4',competition_key='GW001|CUS|DOMESTIC|league|4' WHERE game_world_id='GW001' AND sm_fixture_id=368724190 AND fingerprint='4272511abe810f050675cf40cfd7cfdb38fdc74aa424b78e87e7b121825be896' AND sm_division='3' AND competition_key='GW001|DOMESTIC|playoff|3';

UPDATE `GW001_IMC Match Report` SET sm_division='4',competition_key='GW001|CUS|DOMESTIC|league|4' WHERE game_world_id='GW001' AND sm_fixture_id=368724191 AND fingerprint='5366b85fe2b5386388bafc58689eab57dd8cda67915bf8d62d08040f8be66105' AND sm_division='4' AND competition_key='GW001|DOMESTIC|playoff|4';

UPDATE `GW001_IMC Match Report` SET sm_division='4',competition_key='GW001|CUS|DOMESTIC|league|4' WHERE game_world_id='GW001' AND sm_fixture_id=368724192 AND fingerprint='053036bfc610ebd27296154b2b7cb9d5f6b114024077eced15a7df0b94b30448' AND sm_division='4' AND competition_key='GW001|DOMESTIC|playoff|4';
