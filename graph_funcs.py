import pandas as pd
from pandas.plotting import table
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.patches import ConnectionPatch
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
import six
import math

def save_image(filename):
    # PdfPages is a wrapper around pdf
    # file so there is no clash and
    # create files with no error.
    p = PdfPages(filename)

    # get_fignums Return list of existing
    # figure numbers
    fig_nums = plt.get_fignums()
    figs = [plt.figure(n) for n in fig_nums]

    # iterating over the numbers in list
    for fig in figs:
        # and saving the files
        fig.savefig(p, format='pdf')

        # close the object
    p.close()

def render_table(data, col_width=3.0, row_height=0.125, font_size=14,
                     header_color='#0073e6', row_colors=['#f1f1f2', 'w'], edge_color='w',
                     bbox=[0, 0.7, 1, 0.3], header_columns=0,
                     ax=None, render_doc_stats=False, title="Table Stats", **kwargs):
    '''
    Used to create pdf table based on df (data argument)
    '''
    if ax is None:
        #size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=(18,10))
        ax.axis('off')

    fig.suptitle(title, fontsize=24, fontweight='bold')
    mpl_table = ax.table(cellText=data.values,bbox=bbox, colLabels=data.columns, loc='center', **kwargs)

    mpl_table.auto_set_font_size(False)

    for k, cell in  six.iteritems(mpl_table._cells):
        cell.set_edgecolor(edge_color)

        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w', fontsize=8.0)
            cell.set_facecolor(header_color)
            cell.set_height(row_height)

            if k[1] == 8: # Set cc_error column color to red
                cell.set_facecolor('#F95656')

        elif render_doc_stats and k[1] == 0:
            cell.set_facecolor(row_colors[k[0] % len(row_colors)])
            cell.set_text_props(horizontalalignment='right', fontsize=8.0, weight='bold')
            cell.set_height(row_height)
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors) ])
            cell.set_text_props(horizontalalignment='center', fontsize=12.0)
            cell.set_height(row_height)
    fig.tight_layout()

    return ax


def create_multiple_charts_per_page(df, page_charts_num=4 ):
    #number_of_pages = math.ceil(total_charts/page_charts_num) # calculaate total pages
    number_of_pages = 1

    color_map = {'CC Error - Uploaded Correct Same Document': '#F95656', 'CC Error - Did Not React': '#FBC4C4', 'CC Error - Uploaded Incorrect New Document': '#E76C6C',
                 'CC OK - Did Not React': '#B9C8FB', 'CC OK - Uploaded Correct New Document': '#4A8CE2', 'CC OK - Uploaded Incorrect New Document': '#7AA7E1',
                 'CC OK - Uploaded Incorrect Same Document': '#62B1E8'}

    for page in range(number_of_pages):
        x, y = 0, 0
        figure, axis = plt.subplots(2, 2, figsize=(18, 10))
        skip_docs = page * 4 # Skip docs processed in previous page
        docs = df['period'].unique()
        docs = docs[skip_docs:]

        for doc in docs:
            doc_df = df.loc[df['period'] == doc]
            #labels = ['1', '2', '3', '4']
            data = doc_df['reaction_count']
            labels = doc_df['reaction']

            colors = ['#F95656', '#4A8CE2', '#F95656', '#4A8CE2']
            overall_ratios = list(doc_df['reaction_%'])
            #tmp_x = list(doc_df['classified_docs'])
            #overall_ratios.append(tmp_x[0])

            for i in range(len(overall_ratios)):
                if overall_ratios[i] == 0:
                    del overall_ratios[i]
                    del labels[i]
                    del colors[i]
                    break



            axis[x,y].pie(data, wedgeprops={'linewidth': 1.0, 'edgecolor': 'white'}, startangle=45, colors=[color_map[col] for col in labels],
                   autopct='%1.1f%%', pctdistance=0.8, labeldistance=2,
                   textprops={'fontweight': 'bold', 'fontsize': 10})

            axis[x,y].set_title(doc, weight='bold')

            # If 9 charts created go to next page
            if (x+1)*(y+1) >= 4:
                break


            # Update chart position
            if y < 1:
                y += 1
            else:
                x += 1
                y = 0

    legend_patches = [mpatches.Patch(color=color_map[label], label=label) for label in color_map]
    figure.suptitle("CC Reactions Breakdown\n(User's response to CC rejection)", fontweight='bold', fontsize=16)
    figure.legend(handles=legend_patches, loc='upper left')

    # Delete empty charts on last page
    remove_empty_charts(figure, axis)


def remove_empty_charts(figure, axis):
    for i in range(len(axis)):
        for z in range(len(axis[i])):
            ax = axis[i][z]
            if ax.has_data():
                continue
            else:
                figure.delaxes(ax)

def create_multiple_charts_per_page_error(df, page_charts_num=4 ):
    df =  df.loc[(df['user_error_stip_%'] > 0) | (df['cc_error_stip_%'] > 0)]
    df.rename(columns={'user_error_stip_%': 'user_error_%', 'cc_error_stip_%': 'cc_error_%'}, inplace=True)
    total_charts = len(df['stip_name'].unique()) # one row = one chart
    number_of_pages = math.ceil(total_charts/page_charts_num) # calculate total pages

    color_map = {'user_error_%': '#4A8CE2', 'cc_error_%': '#F95656'}

    for page in range(number_of_pages):
        x, y = 0, 0
        figure, axis = plt.subplots(2, 2, figsize=(18, 10))
        figure.suptitle("CC Rejections Error Distribution", fontweight='bold', fontsize=16)
        skip_docs = page * 4 # Skip docs processed in previous page
        periods = df['stip_name'].unique()
        periods.sort() # To get Grand Total as first chart

        periods = periods[skip_docs:]

        legend_patches = [mpatches.Patch(color=color_map[label], label=label) for label in color_map]
        figure.legend(handles=legend_patches, loc='upper left')


        for doc in periods:
            doc_df = df.loc[df['stip_name'] == doc]

            doc_df.plot(kind='bar', stacked=True, ax=axis[x,y],  x='period', y=['user_error_%', 'cc_error_%'], fontsize=8, rot=20, color=['#4A8CE2', '#F95656'])
            axis[x,y].set_facecolor('#CBCACA')
            axis[x, y].set_title(doc, fontweight='bold')
            axis[x, y].set_xlabel('')
            axis[x, y].legend([])

            # Display % values on bars
            for c in axis[x,y].containers:
                # Optional: if the segment is small or 0, customize the labels
                labels = [str(round(v.get_height(), 2)) + "%" if v.get_height() > 0 else '' for v in c]
                axis[x,y].bar_label(c, labels=labels, label_type='center', weight='bold', color='w')


            # Add alerts count on top of every 100% bar
            total_alerts = doc_df['total_rejected'].tolist()
            top_bars_start = (len(axis[x,y].patches)) / 2 # /2 because bar has 2 values (user/cc error %)
            current_bar = 0
            for p in axis[x,y].patches:
                if current_bar >= top_bars_start:
                    axis[x,y].annotate(f"({total_alerts.pop(0)} docs)", (p.get_x() + p.get_width() / 2, 100),
                                ha='center', va='bottom',
                                fontsize=8, color='black', weight='bold')
                current_bar += 1


            # If 4 charts created go to next page
            if (x + 1) * (y + 1) >= 4:
                break

            # Update chart position
            if y < 1:
                y += 1
            else:
                x += 1
                y = 0

        # Delete empty charts on last page
        remove_empty_charts(figure, axis)

def create_multiple_charts_per_page_new_upload_historical(df, page_charts_num=4 ):
    total_charts = len(df['stip_name'].unique()) # one row = one chart
    number_of_pages = math.ceil(total_charts/page_charts_num) # calculate total pages


    # 'Uploaded same (correct) doc':'#F95656',
    color_map = {
                 'Uploaded Correct Same Document': '#4C86F3',
                 'Uploaded Incorrect Same Document': '#C5D8FB',
                 'Uploaded Correct New Document': '#3570DE',
                 'Uploaded Incorrect New Document': '#86ADF5',
                 'Did Not React': '#A3A5A9'
                 }


    for page in range(number_of_pages):
        x, y = 0, 0
        figure, axis = plt.subplots(2, 2, figsize=(18, 10))
        figure.suptitle("New upload reaction distribution", fontweight='bold', fontsize=16)
        skip_docs = page * 4 # Skip docs processed in previous page
        periods = df['stip_name'].unique()
        periods.sort() # To get Grand Total as first chart

        periods = periods[skip_docs:]

        legend_patches = [mpatches.Patch(color=color_map[label], label=label) for label in color_map]
        figure.legend(handles=legend_patches, loc='upper left')


        for doc in periods:
            print(doc)
            doc_df = df.loc[df['stip_name'] == doc]
            print (doc_df)
            pivot_df = doc_df.pivot(index='period', columns='reaction', values='user_reaction_%').fillna(0)

            pivot_df.plot(kind='bar', stacked=True, ax=axis[x,y], fontsize=8, rot=20, color=[color_map[col] for col in doc_df.reaction.unique()])
            axis[x,y].set_facecolor('#CBCACA')
            axis[x, y].set_title(doc, fontweight='bold')
            axis[x, y].set_xlabel('')
            axis[x, y].legend([])

            # Display % values on bars
            for c in axis[x,y].containers:
                # Optional: if the segment is small or 0, customize the labels
                labels = [str(round(v.get_height(), 2)) + "%" if v.get_height() > 0 else '' for v in c]
                axis[x,y].bar_label(c, labels=labels, label_type='center', weight='bold', color='w')

            # Add stips count on top of every 100% bar
            #total_stips = doc_df[['period', 'user_reaction_count']].sort_values(by='period').drop_duplicates()
            total_stips = doc_df[['period', 'user_reaction_count']].groupby('period')['user_reaction_count'].sum().reset_index()

            total_stips = total_stips['user_reaction_count'].astype(int).tolist()

            total_stips_count = len(total_stips)
            total_bars_count = len(axis[x,y].patches)
            current_bar = 0
            top_bars_start = total_bars_count - total_stips_count

            for p in axis[x,y].patches:
                print (current_bar, top_bars_start)
                if current_bar >= top_bars_start:
                    axis[x,y].annotate(f"Total docs: {total_stips.pop(0)}", (p.get_x() + p.get_width() / 2, 100),
                                ha='center', va='bottom', fontsize=8, color='black', weight='bold')
                current_bar += 1


            # If 4 charts created go to next page
            if (x + 1) * (y + 1) >= 4:
                break

            # Update chart position
            if y < 1:
                y += 1
            else:
                x += 1
                y = 0

        # Delete empty charts on last page
        remove_empty_charts(figure, axis)


def validate_color_codes(my_colors):
    # Used for pie chart RGB color by %
    # Prevents error if color % calculation gets > 100%
    for e in range(len(my_colors)):
        color_code = list(my_colors[e])
        for i in range(3):
            if color_code[i] > 1:
                color_code[i] = 1
        my_colors[e] = (color_code)


def create_reactions_pie_chart(df_reactions):
    fig1 = plt.figure()
    df_len = len(df_reactions.groupby('reaction')['reaction_count'].sum())
    color_map = {'CC Error - Uploaded Correct Same Document': '#F95656', 'CC Error - Did Not React': '#FBC4C4',
                 'CC Error - Uploaded Incorrect New Document': '#E76C6C',
                 'CC OK - Did Not React': '#B9C8FB', 'CC OK - Uploaded Correct New Document': '#4A8CE2',
                 'CC OK - Uploaded Incorrect New Document': '#7AA7E1', 'CC OK - Uploaded Incorrect Same Document': '#62B1E8',
                 'Other issues (rate < 1%)': '#A7A7A7'}


    overall_issues_df = df_reactions.groupby('reaction')['reaction_count'].sum().sort_values(ascending=False).reset_index()
    overall_issues_df['issue_%'] = overall_issues_df['reaction_count'] / overall_issues_df['reaction_count'].sum() * 100
    overall_issues_df['reaction'] = np.where(overall_issues_df['issue_%'] < 1, "Other issues (rate < 1%)", overall_issues_df['reaction'])
    overall_issues_df = overall_issues_df.groupby('reaction')['reaction_count'].sum().sort_values(ascending=False)



    overall_issues_df.plot(kind='pie', ylabel='', pctdistance=0.9, labeldistance=1.15, autopct='%1.1f%%', figsize=(18, 10), fontsize=12, startangle=5,
                           wedgeprops={'linewidth': 1.0, 'edgecolor': 'white'},
                           textprops={'fontweight': 'bold'},
                           colors=[color_map[col] for col in overall_issues_df.index])
    fig1.suptitle("CC Reactions Breakdown\n(User's response to CC rejection)", fontweight='bold', fontsize=16)


def create_stacked_bar_chart_new_uploads(df):

    pivot_df = df.pivot(index='stip_name', columns='new_upload_reaction', values='reaction_%').fillna(0)

    bar_count = len(pivot_df)




    # Define a custom color map for col2 values
    color_map = {'Uploaded same (correct) doc': '#F95656', 'Uploaded same wrong doc': '#FBC4C4', 'Uploaded new wrong doc': '#B9C8FB', 'Uploaded new (correct) doc':'#4A8CE2'}
    if bar_count <= 20:
        ax = pivot_df.plot(kind='bar', stacked=True, figsize=(18, 10), fontsize=8, rot=20, color=[color_map[col] for col in pivot_df.columns])
        ax.set_facecolor('#CBCACA')
        plt.title("New upload reaction distribution", fontsize=16)  # Add the chart title
        plt.legend(loc='lower right', bbox_to_anchor=(1.0, 0.0))

        # Display values on bars
        for c in ax.containers:

            # Optional: if the segment is small or 0, customize the labels
            labels = [str(round(v.get_height(), 2)) + "%" if v.get_height() > 0 else '' for v in c]

            #labels = df['display_value']
            ax.bar_label(c, labels=labels, label_type='center', weight='bold', color='black')

        # Add stips count on top of every 100% bar
        total_stips = df[['stip_name', 'new_upload_doc_count']].sort_values(by='stip_name').drop_duplicates()
        total_stips = total_stips['new_upload_doc_count'].astype(int).tolist()

        total_stips_count = len(total_stips)
        total_bars_count = len(ax.patches)
        current_bar = 0
        top_bars_start = total_bars_count - total_stips_count

        for p in ax.patches:
            if current_bar >= top_bars_start:
                ax.annotate(f"Total docs: {total_stips.pop(0)}", (p.get_x() + p.get_width() / 2, 100), ha='center', va='bottom', fontsize=12, color='black', weight='bold')
            current_bar += 1



    else: # Split chart on multiple pages
        number_of_pages = math.ceil(bar_count / 20)  # calculate total pages
        bars_per_page = math.ceil(bar_count/number_of_pages)


        for page in range(number_of_pages):
            start_bar = page * bars_per_page
            if start_bar + bars_per_page < len(init_df):
                last_bar = start_bar + bars_per_page
            else:
                last_bar = len(init_df)


            df = init_df[start_bar:last_bar]

            fig = df.plot(kind='bar', stacked=True, figsize=(18, 10), title=f"Document Error Rate (page {page + 1})", x='new_upload_reaction', fontsize=8, rot=20, color=['#4A8CE2', '#F95656'])
            fig.set_facecolor('#CBCACA')
            for c in fig.containers:
                # Optional: if the segment is small or 0, customize the labels
                labels = [str(round(v.get_height(), 2)) + "%" if v.get_height() > 0 else '' for v in c]

                # remove the labels parameter if it's not needed for customized labels
                fig.bar_label(c, labels=labels, label_type='center', weight='bold', color='w')


def create_stacked_bar_chart_reactions(df, title):
    init_df = df

    pivot_df = df.pivot(index='stip_name', columns='reaction', values='user_reaction_%').fillna(0)

    bar_count = len(pivot_df)

    # Define a custom color map for col2 values
    color_map = {'CC Error - Did Not React': '#F93333',
                 'CC Error - Uploaded Correct Same Document': '#F88D8D',
                 'CC Error - Uploaded Incorrect New Document': '#FBC4C4',
                 'CC OK - Did Not React': '#4A8CE2',
                 'CC OK - Uploaded Correct New Document': '#86ADF5',
                 'CC OK - Uploaded Incorrect New Document': '#C5D8FB',
                 'CC OK - Uploaded Incorrect Same Document': '#E7EFFC',
                 'Uploaded Correct Same Document':'#4C86F3',
                 'Uploaded Incorrect Same Document': '#C5D8FB',
                 'Uploaded Correct New Document': '#3570DE',
                 'Uploaded Incorrect New Document': '#86ADF5',
                 'Did Not React': '#A3A5A9'
                 }
    if bar_count <= 20:
        ax = pivot_df.plot(kind='bar', stacked=True, figsize=(18, 10), fontsize=8, rot=20, color=[color_map[col] for col in pivot_df.columns])
        ax.set_facecolor('#CBCACA')
        plt.title(title, fontsize=16)  # Add the chart title

        plt.legend(loc='lower right', bbox_to_anchor=(1.0, 0.0))
        # Display values on bars

        for c in ax.containers:
            # Optional: if the segment is small or 0, customize the labels
            labels = [str(round(v.get_height(), 2)) + "%" if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center', weight='bold', color='black')

        # Add stips count on top of every 100% bar
        total_stips = df[['stip_name', 'total_stips']].sort_values(by='stip_name').drop_duplicates()
        total_stips = total_stips['total_stips'].astype(int).tolist()

        total_stips_count = len(total_stips)
        total_bars_count = len(ax.patches)
        current_bar = 0
        top_bars_start = total_bars_count - total_stips_count

        for p in ax.patches:
            if current_bar >= top_bars_start:
                ax.annotate(f"Total docs: {total_stips.pop(0)}", (p.get_x() + p.get_width() / 2, 100), ha='center',
                            va='bottom', fontsize=12, color='black', weight='bold')
            current_bar += 1



    else: # Split chart on multiple pages
        number_of_pages = math.ceil(bar_count / 20)  # calculate total pages
        bars_per_page = math.ceil(bar_count/number_of_pages)


        for page in range(number_of_pages):
            start_bar = page * bars_per_page
            if start_bar + bars_per_page < len(pivot_df):
                last_bar = start_bar + bars_per_page
            else:
                last_bar = len(pivot_df)


            df = pivot_df[start_bar:last_bar]

            fig = df.plot(kind='bar', stacked=True, figsize=(18, 10), title=f"{title} (page {page + 1})", x='stip_name', fontsize=8, rot=20, color=['#4A8CE2', '#F95656'])
            fig.set_facecolor('#CBCACA')
            for c in fig.containers:
                # Optional: if the segment is small or 0, customize the labels
                labels = [str(round(v.get_height(), 2)) + "%" if v.get_height() > 0 else '' for v in c]

                # remove the labels parameter if it's not needed for customized labels
                fig.bar_label(c, labels=labels, label_type='center', weight='bold', color='w')


def create_stacked_bar_chart_errors(df):
    df.sort_values(by='stip_name', inplace=True)
    bar_count = len(df)
    init_df = df
    df = init_df[['stip_name', 'user_error_stip_%', 'cc_error_stip_%']]
    df.rename(columns={'user_error_stip_%': 'user_error_%', 'cc_error_stip_%': 'cc_error_%'}, inplace=True)
    if bar_count <= 20:
        fig, ax = plt.subplots(figsize=(18, 10))
        df.plot(kind='bar', stacked=True, ax=ax, x='stip_name', fontsize=8, rot=20, color=['#4A8CE2', '#F95656'])
        ax.set_facecolor('#CBCACA')
        plt.title("CC Rejections Error Distribution", fontsize=16)  # Add the chart title

        # Display values on bars
        for c in ax.containers:
            # Optional: if the segment is small or 0, customize the labels
            labels = [str(round(v.get_height(), 2)) + "%" if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center', weight='bold', color='w')

        # Add "XYZ" on top of every 100% bar
        total_alerts = init_df['total_rejected'].astype(int).tolist()
        top_bars_start = (len(ax.patches)) / 2
        current_bar = 0
        for p in ax.patches:
            if current_bar >= top_bars_start:
                ax.annotate(f"Total docs: {total_alerts.pop(0)}", (p.get_x() + p.get_width() / 2, 100), ha='center', va='bottom',
                            fontsize=12, color='black', weight='bold')
            current_bar += 1

        plt.legend(loc='lower right', bbox_to_anchor=(1.0, 0.0))
