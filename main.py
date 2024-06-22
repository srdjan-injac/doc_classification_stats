import sqlalchemy
from  urllib.parse  import quote_plus as urlquote
from datetime import date, datetime
import datetime as dt
import pandas as pd
import numpy as np
import configparser
from sql_queries import *
from stats_funcs import stips_map

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

def set_deal_type(deal_type_vin_id, deal_type_id, deal_type_vin, deal_type_appraisal_vin):
    if deal_type_vin_id and deal_type_vin_id != '':
        return deal_type_vin_id
    elif deal_type_id and deal_type_id != '':
        return deal_type_id
    elif deal_type_vin and deal_type_vin != '':
        return deal_type_vin
    elif deal_type_appraisal_vin and deal_type_appraisal_vin != '':
        return deal_type_appraisal_vin
    else:
        return "Unknown deal_type"

def download_data(period_start, period_end):
    # Download Redshift data for creating reports and stats
    period_start = period_start
    period_end = period_end

    requested_docs_path = configParser.get('PATHS', 'requested_docs_path')
    quotes_docs_path = configParser.get('PATHS', 'quotes_docs_path')

    sfpdb_username = configParser.get('SFPDB_CONF', 'username')
    sfpdb_password = configParser.get('SFPDB_CONF', 'password')
    sfpdb_db_path = configParser.get('SFPDB_CONF', 'db_path')

    dev_username = configParser.get('DEV_DB_CONF', 'username')
    dev_password = configParser.get('DEV_DB_CONF', 'password')
    dev_db_path = configParser.get('DEV_DB_CONF', 'db_path')

    conn_sfpdb = sqlalchemy.create_engine(f'postgresql://{sfpdb_username}:{urlquote(sfpdb_password)}@{sfpdb_db_path}')
    conn_dev = sqlalchemy.create_engine(f'postgresql://{dev_username}:{urlquote(dev_password)}@{dev_db_path}')



    # Download data
    print ("Downloading full upload data to ", requested_docs_path)

    query_weekly_data = query_full_data.format(period_start=period_start, period_end=period_end)
    print("QUERY: \n", query_weekly_data)

    df_docs = pd.read_sql(query_weekly_data, conn_sfpdb)

    print ("Downloading quotes data to ", quotes_docs_path)
    df_quotes = pd.read_sql(query_quotes2, conn_dev)

    # Export data
    df_docs.to_csv(requested_docs_path, sep='\t', index=False)
    df_quotes.to_csv(quotes_docs_path, sep='\t', index=False)
    print ("Done!")

def set_stip_name(document_name):
    for stip_name, documents in stips_map.items():
        if document_name in documents:
            return stip_name
    return f"Unknown Document Name - {document_name}"

if __name__ == '__main__':
    # Initialize config
    configParser = configparser.RawConfigParser()
    paths_config = r'init.conf'
    configParser.read(paths_config)

    # Set paths
    requested_docs_path = configParser.get('PATHS', 'requested_docs_path')
    quotes_docs_path = configParser.get('PATHS', 'quotes_docs_path')
    appraisal_docs_path = configParser.get('PATHS', 'appraisal_docs_path')
    products_docs_path = configParser.get('PATHS', 'products_docs_path')
    doc_names_path = configParser.get('PATHS', 'doc_names_path')
    final_data_path = configParser.get('PATHS', 'final_data_path')
    np_report_path = configParser.get('PATHS', 'np_export_report_path')
    sb_report_path = configParser.get('PATHS', 'sb_export_report_path')

    # Set start/end dates
    #period_end = date.today()
    #period_start = period_end - dt.timedelta(days=7)
    period_start = '2023-12-13'
    period_end = '2023-12-20'

    # Download data
    #download_data(str(period_start), str(period_end))
    #raise SystemExit

    # Create dfs
    df_docs = pd.read_csv(requested_docs_path, sep='\t')
    print ("Total validated: ", df_docs.shape)

    df_quotes = pd.read_csv(quotes_docs_path, sep='\t', low_memory=False)
    df_quotes.drop_duplicates(['final_vin', 'deal_id_c'], keep='last', inplace=True)
    #df_quotes = df_quotes[['final_vin', 'deal_id_c', 'opportunity_record_type_c']]



    # Set deal type
    print ("Merging data per VIN + deal_id...")
    df_quotes2 = df_quotes.loc[(df_quotes.deal_id_c.notnull()) & (df_quotes.deal_id_c != '')]
    df_full = df_docs.merge(df_quotes2[['final_vin', 'deal_id_c', 'opportunity_record_type_c']], left_on=['deal_id', 'vin'], right_on=['deal_id_c', 'final_vin'], how='left')
    df_full.rename(columns={'opportunity_record_type_c': 'deal_type_vin_id'}, inplace=True)
    print(df_full.shape)

    df_deal_ids = df_quotes[['deal_id_c', 'opportunity_record_type_c']].loc[(df_quotes.deal_id_c.notnull()) & (df_quotes.deal_id_c != '')].drop_duplicates()

    df_full = df_full.merge(df_deal_ids, left_on=['deal_id'], right_on=['deal_id_c'], how='left')
    df_full.rename(columns={'opportunity_record_type_c': 'deal_type_id'}, inplace=True)
    print(df_full.shape)

    print("Merging data per quotes VIN...")
    df_vin = df_quotes[['final_vin', 'opportunity_record_type_c']].loc[df_quotes.final_vin.notnull()].drop_duplicates('final_vin', keep='last')
    df_full = df_full.merge(df_vin, left_on=['vin'], right_on=['final_vin'], how='left')
    df_full.rename(columns={'opportunity_record_type_c': 'deal_type_vin'}, inplace=True)
    print(df_full.shape)

    print("Merging data per appraisal VIN...")
    df_vin = df_quotes[['appraisal_vin', 'opportunity_record_type_c']].loc[df_quotes.final_vin.notnull()].drop_duplicates('appraisal_vin', keep='last')
    df_full = df_full.merge(df_vin, left_on=['vin'], right_on=['appraisal_vin'], how='left')
    df_full.rename(columns={'opportunity_record_type_c': 'deal_type_appraisal_vin'}, inplace=True)
    print(df_full.shape)

    # Set final deal_type
    df_full.fillna('', inplace=True)
    df_full['deal_type'] = df_full.apply(lambda row: set_deal_type(row['deal_type_vin_id'], row['deal_type_id'], row['deal_type_vin'], row['deal_type_appraisal_vin']), axis=1)


    # Try to get deal type for unmapped VINs by appraisal table
    vins_missing_deal_type = list(df_full['vin'].loc[df_full.deal_type == 'Unknown deal_type'].drop_duplicates())
    print (vins_missing_deal_type)

    dev_username = configParser.get('DEV_DB_CONF', 'username')
    dev_password = configParser.get('DEV_DB_CONF', 'password')
    dev_db_path = configParser.get('DEV_DB_CONF', 'db_path')
    conn_dev = sqlalchemy.create_engine(f'postgresql://{dev_username}:{urlquote(dev_password)}@{dev_db_path}')

    query_missing = query_appraisal_missing_vins.format(vins_list=tuple(vins_missing_deal_type))
    df_missing_dt = pd.read_sql(query_missing, conn_dev)
    df_missing_dt.sort_values(by='appraise_create_date', ascending=False)
    df_missing_dt.drop_duplicates('vin', keep='first', inplace=True)
    df_missing_dt = df_missing_dt[['vin', 'rt_deal_type']]

    df_full = df_full.merge(df_missing_dt, on='vin', how='left')
    df_full['deal_type'] = np.where(df_full['deal_type'] == 'Unknown deal_type', df_full['rt_deal_type'], df_full['deal_type'])

    print (df_missing_dt)

    # Clean data
    df_full.drop(columns=['final_vin_y', 'deal_id_c_y'], inplace=True)
    df_full.rename(columns={'final_vin_x': 'final_vin', 'deal_id_c_x':'deal_id_c'}, inplace=True)

    # Create fake deal_ids based on vin + user_id for stats
    df_full['deal_id'] = np.where(df_full.deal_id == '', df_full.vin.astype('str') + df_full.user_id.astype('str'), df_full.deal_id)

    # Set stip names
    df_full['stip_name'] = df_full.apply(lambda row: set_stip_name(row['name']), axis=1)

    # Normalize rejection reasons
    df_full['rejection_reasons_clean'] = np.where(df_full['rejection_reasons'].str.contains("name"), 'Name Mismatch', df_full['rejection_reasons'])
    df_full['rejection_reasons_clean'] = np.where(df_full['rejection_reasons_clean'].str.contains("does not appear to be the correct type of document"), 'Doc Type Mismatch', df_full['rejection_reasons_clean'])
    df_full['rejection_reasons_clean'] = np.where(df_full['rejection_reasons_clean'].str.contains("expired"), 'Expired Doc', df_full['rejection_reasons_clean'])

    # Export full data for debugging
    df_full.to_csv(final_data_path, sep='\t', index=False)

    # Modify header for reports
    df_full['correctly_rejected'] = ''
    df_full['correct_new_upload'] = ''
    df_full['same_document_uploaded'] = ''
    df_full['comment_first_upload'] = ''
    df_full['comment_second_upload'] = ''

    df_full = df_full[['created', 'name', 'stip_name', 'vin', 'user_response', 'file_id', 'status', 'document_owner_type', 'deal_id',
                        'second_upload', 'rejected_file_id', 'rejected_reason_created_by', 'rejection_reasons_clean', 'created_by', 'updated_by', 'deal_type',
                       'correctly_rejected', 'correct_new_upload', 'same_document_uploaded', 'comment_first_upload', 'comment_second_upload']]

    # Create reports for check
    df_np_report = df_full.loc[(df_full.rejection_reasons_clean.notnull()) & (df_full.created_by == 'cc-autoqa') & (df_full.deal_type == 'Customer Buying / Trading')]
    df_sb_report = df_full.loc[(df_full.rejection_reasons_clean.notnull()) & (df_full.created_by == 'cc-autoqa') & (df_full.deal_type == 'Customer Selling')]

    df_np_report.to_csv(np_report_path, sep='\t', index=False)
    df_sb_report.to_csv(sb_report_path, sep='\t', index=False)
