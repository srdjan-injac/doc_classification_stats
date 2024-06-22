
query_full_data = """
SELECT
rd.created,
rd.name,
rda.vin,
rda.user_id,
rda.deal_id,
rd.file_id,
rd.status,
rd.document_owner_type,
CASE 
    WHEN rd.status = 'Requested' THEN 'No Response'
    WHEN rd.status = 'AutoQAValidated' THEN 'Response'
END AS user_response,
CASE
    WHEN rd.file_id IS NULL AND rd.status = 'AutoQAValidated' THEN 'Continue With Existing Doc'
    WHEN rd.file_id IS NOT NULL THEN 'Upload New Doc'
END AS second_upload,
rjd.file_id AS rejected_file_id,
rjd.rejected_document_id,
string_agg(drr.created_by, ',') AS rejected_reason_created_by,
string_agg(drr.reason, ',') AS rejection_reasons,
rd.created_by, 
rd.updated_by
FROM requester.requested_document rd
INNER JOIN requester.requested_document_association rda ON rda.requested_document_id = rd.requested_document_id
LEFT OUTER JOIN requester.rejected_document rjd ON rjd.new_requested_document_id = rd.requested_document_id
LEFT OUTER JOIN requester.document_rejected_reason drr ON drr.rejected_document_id = rjd.rejected_document_id
WHERE rd.created >= '{period_start}'
AND rd.created < '{period_end}'
GROUP BY 
rd.created,
rd.name,
rda.vin,
rda.user_id,
rda.deal_id,
rd.file_id,
rd.status,
rd.document_owner_type,
rjd.file_id,
rd.created_by,
rd.updated_by,
rjd.rejected_document_id
"""

query_deal_type_prod = """
SELECT distinct prod.vin_c as vin, op.created_date, op.xke_deal_id as deal_id, rt.name as deal_type
FROM dbt_staging.stg_salesforce__opportunities op
JOIN dbt_staging.stg_salesforce__products prod
ON op.vehicle_inventory_id_c = prod.inventory_id_c
LEFT JOIN dbt_staging.stg_salesforce__record_types rt
ON op.record_type_id = rt.id
WHERE op.created_date >= '2023-01-01'
AND vin IS NOT NULL
AND deal_id IS NOT NULL
"""


query_appraisal = """
SELECT ap.vin_c as vin, ap.received_at as appraise_received_at, ap.created_date as appraise_create_date, ap.form_c, 
op.id as opp_id, op.xke_deal_id as deal_id, op.record_type_id, op.created_date as opp_created_date,
rt.name as rt_deal_type
FROM dbt_staging.stg_salesforce__appraisals ap
LEFT JOIN dbt_staging.stg_salesforce__opportunities op
ON ap.opportunity_c = op.id
LEFT JOIN dbt_staging.stg_salesforce__record_types rt
ON op.record_type_id = rt.id
WHERE ap.vin_c IS NOT NULL
AND ap.received_at >= '2023-01-01'
"""

query_opp_products = """
SELECT distinct prod.vin_c as vin, op.created_date as opp_created_date, op.xke_deal_id as deal_id, rt.name as deal_type
FROM dbt_staging.stg_salesforce__opportunities op
JOIN dbt_staging.stg_salesforce__products prod
ON op.vehicle_inventory_id_c = prod.inventory_id_c
LEFT JOIN dbt_staging.stg_salesforce__record_types rt
ON op.record_type_id = rt.id
WHERE op.created_date >= '2023-11-01'
AND prod.vin_c IS NOT NULL
AND deal_type IS NOT NULL
"""

query_doc_names = """
SELECT di.dmv_id, di.document_instance_id, di.created as di_created, 
       dc.document_name, dc.confidence, dc.created as dc_created
FROM document.document_instance AS di
LEFT JOIN document.document_classification AS dc
ON di.document_instance_id = dc.document_instance_id
WHERE dc.confidence > 50
AND di.created >= '{period_start}'
AND di.dmv_id IS NOT NULL
"""

query_doc_names2 = """
SELECT di.dmv_id, di.document_instance_id, di.created as di_created, 
       dc.document_name, dc.confidence, dc.created as dc_created
FROM document.document_instance AS di
LEFT JOIN document.document_classification AS dc
ON di.document_instance_id = dc.document_instance_id
WHERE dc.confidence > 50
AND di.created >= '{period_start}'
AND di.dmv_id IS NOT NULL
"""

query_quotes = """
SELECT q.vehicle_vin_c AS quotes_vin_c, q.vin AS quotes_vin, a.vin_c AS appraisal_vin, 
q.opportunity_record_type_c, q.opportunity_id, q.deal_id_c, q.account_id, q.vehicle_inventory_id_c,
CASE
    WHEN q.vehicle_vin_c IS NULL AND q.vin IS NULL THEN a.vin_c
    WHEN q.vehicle_vin_c IS NOT NULL THEN q.vehicle_vin_c
    WHEN q.vehicle_vin_c IS NULL THEN q.vin
END AS final_vin
FROM dbt_staging.stg_salesforce__quotes q
LEFT JOIN dbt_staging.stg_salesforce__appraisals a
ON q.opportunity_id = a.opportunity_c
WHERE q.created_date >= '2023-12-06'
AND q.created_date < '2023-12-13'
"""

query_quotes2 = """
SELECT q.vehicle_vin_c AS quotes_vin_c, q.vin AS quotes_vin, a.vin_c AS appraisal_vin, 
q.opportunity_record_type_c, q.opportunity_id, q.deal_id_c,
CASE
    WHEN q.vehicle_vin_c IS NULL AND q.vin IS NULL THEN a.vin_c
    WHEN q.vehicle_vin_c IS NOT NULL THEN q.vehicle_vin_c
    WHEN q.vehicle_vin_c IS NULL THEN q.vin
END AS final_vin
FROM dbt_staging.stg_salesforce__quotes q
LEFT JOIN dbt_staging.stg_salesforce__appraisals a
ON q.opportunity_id = a.opportunity_c
WHERE q.created_date >= '2023-10-10'
"""

query_appraisal_missing_vins = """
SELECT ap.vin_c as vin, ap.received_at as appraise_received_at, ap.created_date as appraise_create_date, ap.form_c, 
op.id as opp_id, op.xke_deal_id as deal_id, op.record_type_id, op.created_date as opp_created_date,
rt.name as rt_deal_type
FROM dbt_staging.stg_salesforce__appraisals ap
LEFT JOIN dbt_staging.stg_salesforce__opportunities op
ON ap.opportunity_c = op.id
LEFT JOIN dbt_staging.stg_salesforce__record_types rt
ON op.record_type_id = rt.id
WHERE ap.vin_c IN {vins_list}
"""