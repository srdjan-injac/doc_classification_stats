import configparser
import pandas as pd
import numpy as np
import re
from datetime import datetime
from graph_funcs import *
from stats_funcs import *

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

def format_display_reaction(df, reaction_name):
    # Used to format reaction value for overall stats as reaction_count (reaction_%)
    try:
        reaction_count = int(df['reaction_count'].loc[df.reaction == reaction_name])
    except:
        reaction_count = 0

    try:
        reaction_percent = float(df['reaction_%'].loc[df.reaction == reaction_name])
    except:
        reaction_percent = 0.00

    return f"{reaction_count} ({reaction_percent}%)"


def format_display_reaction2(df, reaction_name):
    # Used to format reaction value for overall stats as reaction_count (reaction_%)

    try:
        reaction_count = int(df['reaction_count'].loc[df.reaction.str.contains(reaction_name) == True].sum())
    except Exception as e:
        print (e)
        reaction_count = 0

    try:
        reaction_percent = float(df['reaction_%'].loc[df.reaction.str.contains(reaction_name) == True].sum())
    except:
        reaction_percent = 0.00

    return f"{reaction_count} ({round(reaction_percent, 2)}%)"


def validate_comments(df):
    bad_df = df.loc[(df['correctly_rejected']=='yes') & (df['correct_new_upload']=='yes') & (df['same_document_uploaded']=='yes')]

    if len(bad_df) > 0:
        print ("Invalid comments combination detected!")
        print (bad_df)
        raise SystemExit


def normalize_yes_no(df, field_name):
    df[field_name] = np.where(df[field_name].str.lower().str.contains("y"), "yes", df[field_name])
    df[field_name] = np.where(df[field_name].str.lower().str.contains("n"), "no", df[field_name])


def generate_reaction(correctly_rejected, correct_new_upload, same_doc_upload):
    if correctly_rejected == "yes" and (correct_new_upload != "/" or same_doc_upload == "yes"):
        return "Uploaded New Document"
    elif correctly_rejected == "no" and same_doc_upload == "yes":
        return "CC Error (Uploaded Same Doc)"
    elif correctly_rejected == "no" and correct_new_upload == "/" and same_doc_upload == "/":
        return "Did Not React (CC Error)"
    elif correctly_rejected == "yes" and correct_new_upload == "/" and same_doc_upload == "/":
        return "Did Not React (CC OK)"
    else:
        print (correctly_rejected, correct_new_upload, same_doc_upload)
        return "Unknown combination"


def generate_reaction2(correctly_rejected, correct_new_upload, same_doc_upload):
    if correctly_rejected == "yes" and correct_new_upload == "yes" :
        return "CC OK - Uploaded Correct New Document"
    elif correctly_rejected == "yes" and correct_new_upload == "no" :
        return "CC OK - Uploaded Incorrect New Document"
    elif correctly_rejected == "yes" and same_doc_upload == "yes" :
        return "CC OK - Uploaded Incorrect Same Document"
    elif correctly_rejected == "yes" and correct_new_upload == "/" and same_doc_upload == "/":
        return "CC OK - Did Not React"
    elif correctly_rejected == "no" and same_doc_upload == "yes":
        return "CC Error - Uploaded Correct Same Document"
    elif correctly_rejected == "no" and correct_new_upload == "no" :
        return "CC Error - Uploaded Incorrect New Document"
    elif correctly_rejected == "no" and correct_new_upload == "/" and same_doc_upload == "/":
        return "CC Error - Did Not React"
    else:
        print (correctly_rejected, correct_new_upload, same_doc_upload)
        return "Unknown combination"


def create_weekly_report(df_full, df_report, deal_type_flag):

    if deal_type_flag not in ['Customer Selling', 'Customer Buying / Trading']:
        return ('Unknown deal type flag!')

    if deal_type_flag == 'Customer Selling':
        stats_path = weekly_stats_path + f"sb_weekly_stats_{file_date_format}.pdf"
        report_title = f"Cruise Control:\nStraight Buy Doc Upload Stats\n({report_period})"
        prev_overall_path = sb_prev_overall_path
        prev_cc_reaction_path = sb_prev_cc_reaction_path
        prev_user_stip_react_path = sb_prev_user_stip_react_path
        prev_user_stip_react_detailed = sb_prev_user_stip_react_detailed_path
        prev_errors_path = sb_prev_errors_path
        prev_new_uploads_path = sb_prev_new_uploads_path

    else:
        stats_path = weekly_stats_path + f"np_weekly_stats_{file_date_format}.pdf"
        report_title = f"Cruise Control:\nNew Purchase Doc Upload Stats\n({report_period})"
        prev_overall_path = np_prev_overall_path
        prev_cc_reaction_path = np_prev_cc_reaction_path
        prev_user_stip_react_path = np_prev_user_stip_react_path
        prev_user_stip_react_detailed = np_prev_user_stip_react_detailed_path
        prev_errors_path = np_prev_errors_path
        prev_new_uploads_path = np_prev_new_uploads_path

    # Get only particular deal_type records & get only data with uploaded files
    df_full = df_full.loc[df_full.deal_type == deal_type_flag]
    df_full = df_full.loc[(df_full.file_id.notnull()) & (df_full.file_id != '')]

    # Normalize checked data
    normalize_yes_no(df_report, 'correctly_rejected')
    normalize_yes_no(df_report, 'correct_new_upload')
    normalize_yes_no(df_report, 'same_document_uploaded')

    # Normalize blank comments
    df_report['correctly_rejected'].fillna('/', inplace=True)
    df_report['correct_new_upload'].fillna('/', inplace=True)
    df_report['same_document_uploaded'].fillna('/', inplace=True)

    # Validate checked report
    validate_comments(df_report)

    # Create reactions column
    df_report['reaction'] = df_report.apply(lambda row: generate_reaction2(row['correctly_rejected'], row['correct_new_upload'], row['same_document_uploaded']), axis=1)


    # Get total numbers used later for Overall stats
    ### Total documents
    total_docs = len(df_full)
    total_uploaded_docs = len(df_full.loc[df_full.status == 'AutoQAValidated'])
    print ("Percentage of validated focs: ", total_uploaded_docs/total_docs*100)
    df_full = df_full.loc[df_full.status == 'AutoQAValidated']

    total_docs_report = len(df_report)
    ### Total uniq deals
    total_deals = df_full.deal_id.nunique()
    total_deals_report = df_report.deal_id.nunique()
    ### Avg docs per deal
    avg_upload_docs_deal = total_uploaded_docs / total_deals




    ################# CC Reaction Stats DF
    df_reactions = df_report.groupby('reaction')['reaction'].count().reset_index(name='reaction_count')
    df_reactions['reaction_%'] = round(df_reactions['reaction_count'] / total_docs_report * 100, 2)


    ################# Stip Code Stats DF
    # Total stips + # and % of wrong docs detected by CC
    df_stips_all = df_full.groupby('stip_name')['stip_name'].count().reset_index(name='total_validated')
    df_stips_report = df_report.groupby('stip_name')['stip_name'].count().reset_index(name='total_rejected')
    # # and % of False positive (determined after report check)
    df_stips_cc_error = df_report.loc[df_report['reaction'].str.contains("CC Error")].groupby('stip_name')['stip_name'].count().reset_index(name='total_cc_errors')
    # Merge data
    df_stips_merged = df_stips_all.merge(df_stips_report, on='stip_name', how='left').fillna(0)
    df_stips_merged = df_stips_merged.merge(df_stips_cc_error, on='stip_name', how='left')
    # Create Grand Total row
    df_stips_merged.loc['Grand Total'] = df_stips_merged.sum(axis=0)
    df_stips_merged['stip_name'].loc['Grand Total'] = 'Grand Total'
    # Calculate % fields
    df_stips_merged['total_rejected_%'] = round(df_stips_merged['total_rejected'] / df_stips_merged['total_validated'] * 100, 2)
    df_stips_merged['cc_accuarcy_%'] =  round(100 - df_stips_merged['total_cc_errors'].fillna(0) / df_stips_merged['total_validated'] * 100, 2)
    df_stips_merged['cc_error_stip_%'] = round(df_stips_merged['total_cc_errors'].fillna(0) / df_stips_merged['total_rejected'] * 100, 2)
    df_stips_merged['total_user_errors'] = df_stips_merged['total_rejected'] - df_stips_merged['total_cc_errors'].fillna(0)
    df_stips_merged['user_error_stip_%'] = round(df_stips_merged['total_user_errors'].fillna(0) / df_stips_merged['total_rejected'] * 100, 2)
    df_stips_merged.fillna(0, inplace=True)



    ################# User's Reactions per stip_code DF including CC accuracy
    df_user_stips_detailed = df_report.groupby(['stip_name', 'reaction'])['reaction'].count().reset_index(name='user_reaction_count')
    df_user_stips_detailed = df_user_stips_detailed.merge(df_stips_merged[['stip_name', 'total_rejected']], on='stip_name', how='left')
    df_user_stips_detailed.rename(columns={'total_rejected': 'total_stips'}, inplace=True)

    # Create Grand Total counts like this since table pivots in the graph funcs...
    df_grand_total_user_reactions = df_user_stips_detailed.groupby('reaction')['user_reaction_count'].sum().reset_index()
    df_grand_total_user_reactions['total_stips'] = df_grand_total_user_reactions['user_reaction_count'].sum()
    df_grand_total_user_reactions['stip_name'] = 'Grand Total'

    df_user_stips_detailed = df_user_stips_detailed.append(df_grand_total_user_reactions)

    df_user_stips_detailed['user_reaction_%'] = round(df_user_stips_detailed['user_reaction_count']/df_user_stips_detailed['total_stips'] * 100, 2)
    df_user_stips_detailed['display_value'] = df_user_stips_detailed['user_reaction_%'].astype(str) + "% (" + df_user_stips_detailed['user_reaction_count'].astype(str) + " docs)"

    ################# User's Reactions per stip_code DF
    tmp_df = df_report
    tmp_df['reaction'] = tmp_df['reaction'].str.replace("CC Error - ", '').str.replace("CC OK - ", '')
    df_user_stips = tmp_df.groupby(['stip_name', 'reaction'])['reaction'].count().reset_index(name='user_reaction_count')
    df_user_stips = df_user_stips.merge(df_stips_merged[['stip_name', 'total_rejected']], on='stip_name', how='left')
    df_user_stips.rename(columns={'total_rejected': 'total_stips'}, inplace=True)
    # Create Grand Total counts like this since table pivots in the graph funcs...
    df_grand_total_user_reactions2 = df_user_stips.groupby('reaction')['user_reaction_count'].sum().reset_index()
    df_grand_total_user_reactions2['total_stips'] = df_grand_total_user_reactions2['user_reaction_count'].sum()
    df_grand_total_user_reactions2['stip_name'] = 'Grand Total'

    df_user_stips = df_user_stips.append(df_grand_total_user_reactions2)
    df_user_stips['user_reaction_%'] = round(df_user_stips['user_reaction_count'] / df_user_stips['total_stips'] * 100,2)
    df_user_stips['display_value'] = df_user_stips['user_reaction_%'].astype(str) + "% (" + df_user_stips['user_reaction_count'].astype(str) + " docs)"



    ################# New upload reaction distribution DF
    df_new_docs = df_report.loc[df_report['reaction'].str.contains("Uploaded") == True]

    df_new_docs['new_upload_reaction'] = np.where((df_new_docs['correctly_rejected']=="yes") & (df_new_docs['same_document_uploaded']=="yes"), "Uploaded same wrong doc", "")
    df_new_docs['new_upload_reaction'] = np.where((df_new_docs['correct_new_upload']=="no") & (df_new_docs['same_document_uploaded']=="no"), "Uploaded new wrong doc", df_new_docs['new_upload_reaction'])
    df_new_docs['new_upload_reaction'] = np.where((df_new_docs['correctly_rejected']=="no") & (df_new_docs['same_document_uploaded']=="yes"), "Uploaded same (correct) doc", df_new_docs['new_upload_reaction'])
    df_new_docs['new_upload_reaction'] = np.where((df_new_docs['correct_new_upload']=="yes") & (df_new_docs['same_document_uploaded']=="no"), "Uploaded new (correct) doc", df_new_docs['new_upload_reaction'])

    df_new_docs_count = df_new_docs.groupby('stip_name')['new_upload_reaction'].count().reset_index(name='new_upload_doc_count')
    df_new_docs_count2 = df_new_docs.groupby(['stip_name', 'new_upload_reaction'])['new_upload_reaction'].count().reset_index(name='new_upload_reaction_count')

    df_new_docs = df_new_docs.merge(df_new_docs_count, on='stip_name', how='left')
    df_new_docs = df_new_docs.merge(df_new_docs_count2, on=['stip_name', 'new_upload_reaction'], how='left')

    df_new_docs = df_new_docs[['stip_name', 'new_upload_reaction', 'new_upload_doc_count', 'new_upload_reaction_count']].drop_duplicates()


    # Create Grand Total counts like this since table pivots in the graph funcs...
    df_grand_total_new_docs = df_new_docs.groupby('new_upload_reaction')['new_upload_reaction_count'].sum().reset_index()
    df_grand_total_new_docs['new_upload_doc_count'] = df_grand_total_new_docs['new_upload_reaction_count'].sum()
    df_grand_total_new_docs['stip_name'] = 'Grand Total'

    df_new_docs = df_new_docs.append(df_grand_total_new_docs)


    df_new_docs['reaction_%'] = round(df_new_docs['new_upload_reaction_count'] / df_new_docs['new_upload_doc_count'] * 100, 2)
    df_new_docs = df_new_docs[['stip_name', 'new_upload_reaction', 'new_upload_doc_count', 'reaction_%']].drop_duplicates()



    ################# Overall stats
    df_total_stats = pd.DataFrame({
                      'period': report_period,
                      'total_validated_docs' : [total_uploaded_docs],
                      'total_deals': [total_deals],
                      'avg_docs_per_deal':[round(avg_upload_docs_deal, 2)],
                      'total_rejected_deals': [total_deals_report],
                      '%_of_rejected_deals': [round(total_deals_report / total_deals * 100, 2)],
                      '%_of_rejected_docs': [round(total_docs_report / total_uploaded_docs * 100, 2)],
                       'total_cc_rejected_docs': [total_docs_report],
                       'cc_error': format_display_reaction2(df_reactions, "CC Error"),
                       'user_error': format_display_reaction2(df_reactions, "CC OK")

    })

    ############## CREATE PDF
    disclaimer = ''
    fig = plt.figure(figsize=(18,10))
    fig.suptitle(report_title, fontsize=24, fontweight='bold', y=0.7)
    fig.text(0.1, 0.2, disclaimer, fontsize=12)

    # Create overall stats table
    render_table(df_total_stats, header_columns=0, col_width=2.0, row_height=0.02, title='Overall Stats')

    # Create Stip Code Stats table
    df_stips_merged['total_cc_errors'] = df_stips_merged['total_cc_errors'].astype('int').astype('str') + " (" + df_stips_merged['cc_error_stip_%'].astype('str') + "%)"
    df_stips_merged['total_user_errors'] = df_stips_merged['total_user_errors'].astype('int').astype('str') + " (" + df_stips_merged['user_error_stip_%'].astype('str') + "%)"
    df_stips_merged['total_rejected'] = df_stips_merged['total_rejected'].astype('int').astype('str')
    render_table(df_stips_merged[['stip_name', 'total_validated', 'total_rejected', 'total_rejected_%', 'cc_accuarcy_%', 'total_cc_errors', 'total_user_errors']], header_columns=0, col_width=2.0, row_height=1, bbox=[0, 0.1, 1, 0.9], title='CC Stats per Document Type', render_doc_stats=True)

    # Create CC Alerts - Error distribution stacked bars chart
    create_stacked_bar_chart_errors(df_stips_merged[['stip_name', 'total_rejected', 'user_error_stip_%', 'cc_error_stip_%']].loc[(df_stips_merged['cc_error_stip_%'] > 0) | (df_stips_merged['user_error_stip_%'] > 0)])

    # Create CC Reactions Stats pie chart
    create_reactions_pie_chart(df_reactions)

    # Create User's Reactions per doc type stacked bars chart
    create_stacked_bar_chart_reactions(df_user_stips, title="User's Reactions per doc type")

    # Create detailed User's Reactions per doc type stacked bars chart
    create_stacked_bar_chart_reactions(df_user_stips_detailed, title="User's Reactions per doc type - breakdown")


    #create_stacked_bar_chart_new_uploads(df_new_docs)

    # Export charts to pdf
    save_image(stats_path)
    plt.close('all')


    # Update historical files with fresh data
    historical_tables = [df_total_stats, df_reactions, df_user_stips, df_user_stips_detailed, df_stips_merged, df_new_docs]

    for hist_tab in historical_tables:
        hist_tab['period'] = report_period
        hist_tab['year'] = year
        hist_tab['record_timestamp'] = current_timestamp

    update_stats_file(prev_overall_path, df_total_stats)
    update_stats_file(prev_cc_reaction_path, df_reactions)
    update_stats_file(prev_user_stip_react_path, df_user_stips)
    update_stats_file(prev_user_stip_react_detailed, df_user_stips_detailed)
    update_stats_file(prev_errors_path, df_stips_merged[['period', 'stip_name', 'total_rejected', 'user_error_stip_%', 'cc_error_stip_%']])
    update_stats_file(prev_new_uploads_path, df_new_docs)

def update_stats_file(file_path, new_df):
    # Func for updating file with full monthly stats
    try:
        full_df = pd.read_csv(file_path, sep='\t')
        updated_df = full_df.append(new_df)
        updated_df.to_csv(file_path, sep='\t', index=False)
    except Exception as e:
        print (e)
        new_df.to_csv(file_path, sep='\t', index=False)


def create_historical_report(deal_type_flag):
    if deal_type_flag not in ['Customer Selling', 'Customer Buying / Trading']:
        return ('Unknown deal type flag!')

    if deal_type_flag == 'Customer Selling':
        report_prefix = 'sb'
    else:
        report_prefix = 'np'

    report_title = f"Cruise Control:\n{report_prefix.upper()} Upload Auto QA Historical Report\n({period_end})"
    disclaimer = ''

    # Files with previous weeks overall stats
    prev_overall_path = configParser.get('PATHS', report_prefix+'_prev_overall_path')
    prev_cc_reaction_path = configParser.get('PATHS', report_prefix+'_prev_cc_reaction_path')
    prev_user_stip_react_path = configParser.get('PATHS', report_prefix+'_prev_user_stip_react_path')
    prev_user_stip_react_detailed = configParser.get('PATHS', report_prefix+'_prev_user_stip_react_detailed_path')
    prev_errors_path = configParser.get('PATHS', report_prefix+'_prev_errors_path')
    prev_new_uploads_path = configParser.get('PATHS', report_prefix+'_prev_new_uploads_path')
    export_dir = configParser.get('PATHS', 'weekly_stats_path')
    export_path = export_dir + f"{report_prefix}_historical_stats_{file_date_format}.pdf"

    # Create Title Page
    fig = plt.figure(figsize=(18, 10))
    fig.suptitle(report_title, fontsize=24, fontweight='bold', y=0.7)
    fig.text(0.1, 0.2, disclaimer, fontsize=12)

    # Create Overall stats table
    df_overall = pd.read_csv(prev_overall_path, sep='\t')
    df_overall.drop(columns=['year', 'record_timestamp'], inplace=True)

    # Cut last 4 weeks for report
    last_4_weeks = df_overall.period.unique()[-4:]

    # Render data
    render_table(df_overall, header_columns=0, col_width=2.0, row_height=0.02, title='Overall Stats')

    # Create CC Reactions (User's response to CC alert) pie charts
    df_cc_reactions = pd.read_csv(prev_cc_reaction_path, sep='\t')
    df_cc_reactions = df_cc_reactions.loc[df_cc_reactions.period.isin(last_4_weeks)]

    create_multiple_charts_per_page(df_cc_reactions)

    # Create CC Alerts Error Distribution stacked bar charts
    df_errors = pd.read_csv(prev_errors_path, sep='\t')
    df_errors = df_errors.loc[df_errors.period.isin(last_4_weeks)]

    create_multiple_charts_per_page_error(df_errors)

    # Create New Upload Decision Distribution stacked bar charts
    df_new_uploads = pd.read_csv(prev_user_stip_react_path, sep='\t')
    df_new_uploads = df_new_uploads.loc[df_new_uploads.period.isin(last_4_weeks)]

    create_multiple_charts_per_page_new_upload_historical(df_new_uploads)

    # Export final report in pdf format
    save_image(export_path)
    plt.close('all')


if __name__ == '__main__':
    # Initialize config
    configParser = configparser.RawConfigParser()
    paths_config = r'init.conf'
    configParser.read(paths_config)

    # Set paths
    full_data_path = configParser.get('PATHS', 'final_data_path')
    np_report_path = configParser.get('PATHS', 'np_checked_report_path')
    sb_report_path = configParser.get('PATHS', 'sb_checked_report_path')
    weekly_stats_path = configParser.get('PATHS', 'weekly_stats_path')

    np_prev_overall_path = configParser.get('PATHS', 'np_prev_overall_path')
    np_prev_cc_reaction_path = configParser.get('PATHS', 'np_prev_cc_reaction_path')
    np_prev_user_stip_react_path = configParser.get('PATHS', 'np_prev_user_stip_react_path')
    np_prev_user_stip_react_detailed_path = configParser.get('PATHS', 'np_prev_user_stip_react_detailed_path')
    np_prev_errors_path = configParser.get('PATHS', 'np_prev_errors_path')
    np_prev_new_uploads_path = configParser.get('PATHS', 'np_prev_new_uploads_path')

    sb_prev_overall_path = configParser.get('PATHS', 'sb_prev_overall_path')
    sb_prev_cc_reaction_path = configParser.get('PATHS', 'sb_prev_cc_reaction_path')
    sb_prev_user_stip_react_path = configParser.get('PATHS', 'sb_prev_user_stip_react_path')
    sb_prev_user_stip_react_detailed_path = configParser.get('PATHS', 'sb_prev_user_stip_react_detailed_path')
    sb_prev_errors_path = configParser.get('PATHS', 'sb_prev_errors_path')
    sb_prev_new_uploads_path = configParser.get('PATHS', 'sb_prev_new_uploads_path')

    # Create DFs
    df_full = pd.read_csv(full_data_path, sep='\t')
    df_np_report = pd.read_csv(np_report_path, sep='\t')
    df_sb_report = pd.read_csv(sb_report_path, sep='\t')

    # Create report period flag + timestamp of stats creation
    period_start = pd.to_datetime(df_full.created.min()).date().strftime('%m/%d')
    period_end = pd.to_datetime(df_full.created.max()).date().strftime('%m/%d')
    report_period = f"{period_start} - {period_end}"
    year = pd.to_datetime(df_full.created.max()).date().strftime('%Y')
    current_timestamp = datetime.now()
    file_date_format = re.sub('/','', period_start) + "_" + re.sub('/','', period_end)

    # Create weekly reports and export pdf stats files
    print ("REPORT PERIOD: ", report_period)
    print ("Creating NP weekly stats...")
    create_weekly_report(df_full, df_np_report, 'Customer Buying / Trading')

    print ("Creating SB weekly stats...")
    create_weekly_report(df_full, df_sb_report, 'Customer Selling')

    print ("Creating NP historical stats...")
    create_historical_report('Customer Buying / Trading')

    print("Creating SB historical stats...")
    create_historical_report('Customer Selling')



