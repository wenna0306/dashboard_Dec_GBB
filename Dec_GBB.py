import openpyxl
import pandas as pd
import plotly.graph_objects as go
import matplotlib
import numpy as np
import streamlit as st
from matplotlib.backends.backend_agg import RendererAgg
matplotlib.use('agg')
from st_btn_select import st_btn_select
import streamlit_authenticator as stauth
_lock = RendererAgg.lock

# -----------------------------------------set page layout-------------------------------------------------------------
st.set_page_config(page_title='iSMM Dashboard',
                   page_icon = ':chart_with_upwards_trend:',
                   layout='wide',
                   initial_sidebar_state='collapsed')


page = st_btn_select(('Faults', 'Schedules', 'Inventories'),
                     nav=True,
                     format_func=lambda name: name.capitalize(),
                     )

#-----------------------------------------------User Authentication-----------------------------------------------
names = ['wenna', 'Lifei', 'Thiru']
usernames = ['wenna0306@gmail.com', 'Lifei', 'Thiru']
passwords = ['password', 'password', 'password']

hashed_passwords = stauth.hasher(passwords).generate()

authenticator = stauth.authenticate(names,usernames,hashed_passwords,
    'some_cookie_name','some_signature_key',cookie_expiry_days=30)

name, authentication_status = authenticator.login('Login','main')

if authentication_status:
    st.write('Welcome *%s*' % (name))

# =============================================Fault================================================
    if page =='Faults':
        html_card_title="""
        <div class="card">
          <div class="card-body" style="border-radius: 10px 10px 0px 0px; padding-top: 5px; width: 600px;
           height: 50px;">
            <h1 class="card-title" style=color:#116a8c; font-family:Georgia; text-align: left; padding: 0px 0;">FAULT DASHBOARD</h1>
          </div>
        </div>
        """

        st.markdown(html_card_title, unsafe_allow_html=True)
        st.markdown('##')
        st.markdown('##')
        st.markdown(
            'Welcome to this Analysis App, get more detail from :point_right: [iSMM](https://ismm.sg/ce/login)')
        st.markdown('##')

        def fetch_file(filename):
            cols = ['Fault Number', 'Building Trade', 'Trade Category',
                    'Type of Fault', 'Impact', 'Location', 'Cancel Status', 'Reported Date',
                    'Fault Acknowledged Date', 'Responded on Site Date', 'RA Conducted Date',
                    'Work Started Date', 'Work Completed Date',
                    'Other Trades Required Date', 'Cost Cap Exceed Date',
                    'Assistance Requested Date', 'Fault Reference',
                    'End User Priority', 'Incident Report', 'Remarks']
            parse_dates = ['Reported Date',
                           'Fault Acknowledged Date', 'Responded on Site Date', 'RA Conducted Date',
                           'Work Started Date', 'Work Completed Date',
                           'Other Trades Required Date', 'Cost Cap Exceed Date',
                           'Assistance Requested Date']
            return pd.read_excel(filename, header=1, index_col='Fault Number', usecols=cols, parse_dates=parse_dates)


        df = fetch_file('Fault 2022-01-02 105614.xlsx')
        df.columns = df.columns.str.replace(' ', '_')
        df['Time_Acknowledged_mins'] = (df.Fault_Acknowledged_Date - df.Reported_Date)/pd.Timedelta(minutes=1)
        df['Time_Site_Reached_mins'] = (df.Responded_on_Site_Date - df.Reported_Date)/pd.Timedelta(minutes=1)
        df['Time_Work_Started_mins'] = (df.Work_Started_Date - df.Reported_Date)/pd.Timedelta(minutes=1)
        df['Time_Work_Recovered_mins'] = (df.Work_Completed_Date - df.Reported_Date)/pd.Timedelta(minutes=1)

        df1 = df.Location.str.split(pat=' > ', expand=True, n=4).rename(columns={0:'Site', 1:'Building', 2:'Level', 3:'Room'})
        df2 = pd.concat([df, df1], axis=1)

        df_outstanding = df2.loc[(df2['Cancel_Status'].isna()) & (df2['Work_Completed_Date'].isna()),:]

        df3 = df2.loc[(df2['Cancel_Status'].isna()) & (df2['Work_Completed_Date'].notna()),:] #recovered faults
        cols_drop = ['Impact', 'Cancel_Status', 'Other_Trades_Required_Date', 'Cost_Cap_Exceed_Date', 'Assistance_Requested_Date',
                     'Fault_Reference', 'End_User_Priority', 'Incident_Report', 'Location', 'Reported_Date', 'Fault_Acknowledged_Date',
                     'Responded_on_Site_Date', 'RA_Conducted_Date', 'Work_Started_Date', 'Work_Completed_Date']
        df3.drop(columns=cols_drop, inplace=True)
        df3 = df3[['Site', 'Building', 'Level', 'Room', 'Building_Trade', 'Trade_Category', 'Type_of_Fault', 'Time_Acknowledged_mins',
                   'Time_Site_Reached_mins', 'Time_Work_Started_mins', 'Time_Work_Recovered_mins']]

        bin_responded = [0, 10, 30, 60, np.inf]
        label_responded = ['0-10mins', '10-30mins', '30-60mins', '60-np.inf']

        bin_recovered = [0, 60, 240, 480, np.inf]
        label_recovered = ['0-1hr', '1-4hrs', '4-8hrs', '8-np.inf']

        df3['KPI_For_Responded'] = pd.cut(df3.Time_Site_Reached_mins, bins=bin_responded, labels=label_responded, include_lowest=True)
        df3['KPI_For_Recovered'] = pd.cut(df3.Time_Work_Recovered_mins, bins=bin_recovered, labels=label_recovered, include_lowest=True)

        df_daily = df2.loc[(df2['Cancel_Status'].isna()) & (df2['Work_Completed_Date'].notna()),:] #some columns is not exist in df3

        # ----------------------------------------Sidebar---------------------------------------------------------------------
        st.sidebar.header('Please Filter Here:')

        Building_Trade = st.sidebar.multiselect(
            'Select the Building Trade:',
            options=df2['Building_Trade'].unique(),
            default=df2['Building_Trade'].unique()
        )

        Trade_Category = st.sidebar.multiselect(
            'Select the Trade Category:',
            options=df2['Trade_Category'].unique(),
            default=df2['Trade_Category'].unique()
        )

        df2 = df2.query(
            'Building_Trade ==@Building_Trade & Trade_Category==@Trade_Category'
        )


        # ----------------------------------------------Main Page---------------------------------------------------------------
        html_card_subheader_outstanding = """
        <div class="card">
          <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #116a8c; padding-top: 5px; width: 350px;
           height: 50px;">
            <h3 class="card-title" style="background-color:#116a8c; color:#eabd1d; font-family:Georgia; text-align: center; padding: 0px 0;">Outstanding Fault</h3>
          </div>
        </div>
        """
        html_card_subheader_daily="""
        <div class="card">
          <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #116a8c; padding-top: 5px; width: 350px;
           height: 50px;">
            <h3 class="card-title" style="background-color:#116a8c; color:#eabd1d; font-family:Georgia; text-align: center; padding: 0px 0;">Daily Fault Cases</h3>
          </div>
        </div>
        """
        html_card_subheader_KPI_Responded="""
        <div class="card">
          <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #116a8c; padding-top: 5px; width: 450px;
           height: 50px;">
            <h3 class="card-title" style="background-color:#116a8c; color:#eabd1d; font-family:Georgia; text-align: center; padding: 0px 0;">KPI Monitoring-Responded</h3>
          </div>
        </div>
        """
        html_card_subheader_KPI_Recovered="""
        <div class="card">
          <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #116a8c; padding-top: 5px; width: 450px;
           height: 50px;">
            <h3 class="card-title" style="background-color:#116a8c; color:#eabd1d; font-family:Georgia; text-align: center; padding: 0px 0;">KPI Monitoring-Recovered</h3>
          </div>
        </div>
        """
        html_card_subheader_Tier1="""
        <div class="card">
          <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #116a8c; padding-top: 5px; width: 500px;
           height: 50px;">
            <h3 class="card-title" style="background-color:#116a8c; color:#eabd1d; font-family:Georgia; text-align: center; padding: 0px 0;">Recovered Fault vs Building Trade</h3>
          </div>
        </div>
        """
        html_card_subheader_Tier2="""
        <div class="card">
          <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #116a8c; padding-top: 5px; width: 500px;
           height: 50px;">
            <h3 class="card-title" style="background-color:#116a8c; color:#eabd1d; font-family:Georgia; text-align: center; padding: 0px 0;">Recovered Fault vs Trade Category</h3>
          </div>
        </div>
        """
        html_card_subheader_Tier3="""
        <div class="card">
          <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #116a8c; padding-top: 5px; width: 500px;
           height: 50px;">
            <h3 class="card-title" style="background-color:#116a8c; color:#eabd1d; font-family:Georgia; text-align: center; padding: 0px 0;">Recovered Fault vs Type of Fault</h3>
          </div>
        </div>
        """
        html_card_subheader_location="""
        <div class="card">
          <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #116a8c; padding-top: 5px; width: 450px;
           height: 50px;">
            <h3 class="card-title" style="background-color:#116a8c; color:#eabd1d; font-family:Georgia; text-align: center; padding: 0px 0;">Recovered Fault vs Location</h3>
          </div>
        </div>
        """

        # -----------------------------------------------------Fault--------------------------------------------------------
        total_fault = df2.shape[0]
        fault_cancelled = int(df2['Cancel_Status'].notna().sum())
        fault_not_recovered = df2.loc[(df2['Cancel_Status'].isna()) & (df2['Work_Completed_Date'].isna()),:].shape[0]
        fault_recovered = df2.loc[(df2['Cancel_Status'].isna()) & (df2['Work_Completed_Date'].notna()),:].shape[0]
        fault_incident = int(df2['Incident_Report'].sum())

        column01_fault, column02_fault, column03_fault, column04_fault, column05_fault = st.columns(5)
        with column01_fault, _lock:
            st.markdown(
                f"<h6 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:bottom; color: #116a8c;'>Total</h6>",
                unsafe_allow_html=True)
            st.markdown(
                f"<h2 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:top; color: #116a8c;'>{total_fault}</h2>",
                unsafe_allow_html=True)

        with column02_fault, _lock:
            st.markdown(
                f"<h6 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:bottom; color: #116a8c;'>Cancelled</h6>",
                unsafe_allow_html=True)
            st.markdown(
                f"<h2 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:top; color: #116a8c;'>{fault_cancelled}</h2>",
                unsafe_allow_html=True)

        with column03_fault, _lock:
            st.markdown(
                f"<h6 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:bottom; color: #116a8c;'>Outstanding</h6>",
                unsafe_allow_html=True)
            st.markdown(
                f"<h2 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:top; color: red;'>{fault_not_recovered}</h2>",
                unsafe_allow_html=True)

        with column04_fault, _lock:
            st.markdown(
                f"<h6 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:bottom; color: #116a8c;'>Recovered</h6>",
                unsafe_allow_html=True)
            st.markdown(
                f"<h2 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:top; color: #116a8c;'>{fault_recovered}</h2>",
                unsafe_allow_html=True)

        with column05_fault, _lock:
            st.markdown(
                f"<h6 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:bottom; color: #116a8c;'>Incident Report</h6>",
                unsafe_allow_html=True)
            st.markdown(
                f"<h2 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:top; color: red;'>{fault_incident}</h2>",
                unsafe_allow_html=True)

#--------------------------------------- color & width & opacity----------------------------------------------
            # all chart
            titlefontcolor = '#116a8c'

            # pie chart for outstanding and tier1
            colorpieoutstanding = ['#116a8c', '#4c9085', '#50a747', '#59656d', '#06c2ac', '#137e6d', '#929906', '#ff9408']
            colorpierecoveredtier1 = ['#116a8c', '#4c9085', '#50a747', '#59656d', '#06c2ac', '#137e6d', '#929906', '#ff9408']

            # all barchart include stack bar chart and individual barchart and linechart
            plot_bgcolor = 'rgba(0,0,0,0)'
            gridwidth = 0.1
            gridcolor = '#1f3b4d'

            # stack barchart
            colorstackbarpass = '#048243'
            colorstackbarfail01 = '#116a8c'
            colorstackbarfail02 = '#ffdb58'
            colorstackbarfail03 = '#fa2a55'

            # individual barchart color, barline color& width, bar opacity
            markercolor = '#116a8c'
            markerlinecolor = '#116a8c'
            markerlinewidth = 1
            opacity01 = 0.6
            opacity02 = 0.7
            opacity03 = 0.9

            # x&y axis width and color
            linewidth_xy_axis = 1
            linecolor_xy_axis = '#59656d'

        # -----------------------------------------Outstanding Fault--------------------------------------------------------
        st.markdown('##')
        st.markdown("""<hr style="height:5px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
        st.markdown(html_card_subheader_outstanding, unsafe_allow_html=True)
        st.markdown('##')

        ser_outstanding_building = df_outstanding.groupby(['Building_Trade'])['Type_of_Fault'].count().sort_values(ascending=False)
        ser_outstanding_category = df_outstanding.groupby(['Trade_Category'])['Type_of_Fault'].count().sort_values(ascending=False)
        st.dataframe(df_outstanding)
        # x_outstanding_building = ser_outstanding_building.index
        # y_outstanding_building = ser_outstanding_building.values
        # x_outstanding_category = ser_outstanding_category.index
        # y_outstanding_category = ser_outstanding_category.values
        #
        # fig_outstanding_building, fig_outstanding_category = st.columns([1, 2])
        #
        # with fig_outstanding_building, _lock:
        #     fig_outstanding_building = go.Figure(data=[go.Pie(labels=x_outstanding_building, values=y_outstanding_building, hoverinfo='all', textinfo='label+percent+value', textfont_size=15, textfont_color='white', textposition='inside', showlegend=False, hole=.4)])
        #     fig_outstanding_building.update_layout(title='Number of Fault vs Building Trade', annotations=[dict(text='Outstanding', x=0.5, y=0.5, font_size=18, showarrow=False)])
        #     st.plotly_chart(fig_outstanding_building, use_container_width=True)
        #
        # with fig_outstanding_category, _lock:
        #     fig_outstanding_category = go.Figure(data=[go.Bar(x=x_outstanding_category, y=y_outstanding_category, orientation='v', text=y_outstanding_category)])
        #     fig_outstanding_category.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color='#4c9085', showgrid=False,
        #                        showline=True, linewidth=1, linecolor='#59656d')
        #     fig_outstanding_category.update_yaxes(title_text='Number of Fault', title_font_color='#4c9085', showgrid=True, gridwidth=0.1,
        #                        gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
        #     fig_outstanding_category.update_traces(marker_color='#4c9085', marker_line_color='#4c9085', marker_line_width=1)
        #     fig_outstanding_category.update_layout(title='Number of Fault vs Trade Category', plot_bgcolor='rgba(0,0,0,0)')
        #     st.plotly_chart(fig_outstanding_category, use_container_width=True)

        st.markdown('##')
        st.markdown("""<hr style="height:5px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)


        # --------------------------------------Daily Fault----------------------------------------------------
        st.markdown(html_card_subheader_daily, unsafe_allow_html=True)
        x_daily = df_daily['Reported_Date'].dt.day.value_counts().sort_index().index
        y_daily = df_daily['Reported_Date'].dt.day.value_counts().sort_index().values
        y_mean = df_daily['Reported_Date'].dt.day.value_counts().sort_index().mean()

        fig_daily = go.Figure(
            data=go.Scatter(x=x_daily, y=y_daily, mode='lines+markers+text', line=dict(color='#116a8c', width=3),
                            text=y_daily, textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                            textposition='top center'))
        fig_daily.add_hline(y=y_mean, line_dash='dot', line_color='#96ae8d', line_width=2, annotation_text='Average Line',
                            annotation_position='bottom right', annotation_font_size=18, annotation_font_color='green')
        fig_daily.update_xaxes(title_text='Date', tickangle=-45, title_font_color=titlefontcolor, tickmode='linear',
                               range=[1, 31],
                               showgrid=False, gridwidth=gridwidth, gridcolor=gridcolor, showline=True,
                               linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
        fig_daily.update_yaxes(title_text='Number of Fault', title_font_color=titlefontcolor, showgrid=False,
                               gridwidth=gridwidth, gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis,
                               linecolor=linecolor_xy_axis)
        fig_daily.update_layout(title='Number of Fault vs Date', plot_bgcolor=plot_bgcolor)
        st.plotly_chart(fig_daily, use_container_width=True)


     #---------------------------------------------KPI Monitoring-------------------------------------------------------

        st.markdown(html_card_subheader_KPI_Responded, unsafe_allow_html=True)
        st.markdown('##')
        st.markdown('Response Time refers to the time the fault or emergency was reported to the time the Contractor arrived on-site with evidence')
        st.markdown('##')

        x_KPI_building_010_Responded = df3.groupby(by='KPI_For_Responded').Building_Trade.value_counts().loc['0-10mins'].index
        x_KPI_building_1030_Responded = df3.groupby(by='KPI_For_Responded').Building_Trade.value_counts().loc['10-30mins'].index
        x_KPI_building_3060_Responded = df3.groupby(by='KPI_For_Responded').Building_Trade.value_counts().loc['30-60mins'].index
        x_KPI_building_60inf_Responded = df3.groupby(by='KPI_For_Responded').Building_Trade.value_counts().loc['60-np.inf'].index

        y_KPI_building_010_Responded = df3.groupby(by='KPI_For_Responded').Building_Trade.value_counts().loc['0-10mins'].values
        y_KPI_building_1030_Responded = df3.groupby(by='KPI_For_Responded').Building_Trade.value_counts().loc['10-30mins'].values
        y_KPI_building_3060_Responded = df3.groupby(by='KPI_For_Responded').Building_Trade.value_counts().loc['30-60mins'].values
        y_KPI_building_60inf_Responded = df3.groupby(by='KPI_For_Responded').Building_Trade.value_counts().loc['60-np.inf'].values

        x_KPI_category_010_Responded = df3.groupby(by='KPI_For_Responded').Trade_Category.value_counts().loc['0-10mins'].index
        x_KPI_category_1030_Responded = df3.groupby(by='KPI_For_Responded').Trade_Category.value_counts().loc['10-30mins'].index
        x_KPI_category_3060_Responded = df3.groupby(by='KPI_For_Responded').Trade_Category.value_counts().loc['30-60mins'].index
        x_KPI_category_60inf_Responded = df3.groupby(by='KPI_For_Responded').Trade_Category.value_counts().loc['60-np.inf'].index

        y_KPI_category_010_Responded = df3.groupby(by='KPI_For_Responded').Trade_Category.value_counts().loc['0-10mins'].values
        y_KPI_category_1030_Responded = df3.groupby(by='KPI_For_Responded').Trade_Category.value_counts().loc['10-30mins'].values
        y_KPI_category_3060_Responded = df3.groupby(by='KPI_For_Responded').Trade_Category.value_counts().loc['30-60mins'].values
        y_KPI_category_60inf_Responded = df3.groupby(by='KPI_For_Responded').Trade_Category.value_counts().loc['60-np.inf'].values

        fig_responded_building, fig_responded_category = st.columns([1, 2])
        with fig_responded_building, _lock:
            fig_responded_building = go.Figure(data=[
                go.Bar(name='0-10mins', x=x_KPI_building_010_Responded, y=y_KPI_building_010_Responded, marker_color=colorstackbarpass),
                go.Bar(name='10-30mins', x=x_KPI_building_1030_Responded, y=y_KPI_building_1030_Responded, marker_color=colorstackbarfail01),
                go.Bar(name='30-60mins', x=x_KPI_building_3060_Responded, y=y_KPI_building_3060_Responded, marker_color=colorstackbarfail02),
                go.Bar(name='60-np.inf', x=x_KPI_building_60inf_Responded, y=y_KPI_building_60inf_Responded, marker_color=colorstackbarfail03)
            ])
            fig_responded_building.update_xaxes(title_text="Building Trade", tickangle=-45, title_font_color=titlefontcolor,
                                                showgrid=False, gridwidth=gridwidth, gridcolor=gridcolor, showline=True,
                                                linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig_responded_building.update_yaxes(title_text='Number of Fault', title_font_color=titlefontcolor, showgrid=True, gridwidth=gridwidth, gridcolor=gridcolor,
                               showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig_responded_building.update_layout(barmode='stack', title='KPI Monitoring(Responded) vs Building Trade', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig_responded_building, use_container_width=True)

        with fig_responded_category, _lock:
            fig_responded_category = go.Figure(data=[
                go.Bar(name='0-10mins', x=x_KPI_category_010_Responded, y=y_KPI_category_010_Responded, marker_color=colorstackbarpass),
                go.Bar(name='10-30mins', x=x_KPI_category_1030_Responded, y=y_KPI_category_1030_Responded, marker_color=colorstackbarfail01),
                go.Bar(name='30-60mins', x=x_KPI_category_3060_Responded, y=y_KPI_category_3060_Responded, marker_color=colorstackbarfail02),
                go.Bar(name='60-np.inf', x=x_KPI_category_60inf_Responded, y=y_KPI_category_60inf_Responded, marker_color=colorstackbarfail03),
            ])
            fig_responded_category.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color=titlefontcolor,
                                                showgrid=False, gridwidth=gridwidth, gridcolor=gridcolor, showline=True,
                                                linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig_responded_category.update_yaxes(title_text='Number of Fault', title_font_color=titlefontcolor, showgrid=True,
                                                gridwidth=gridwidth, gridcolor=gridcolor, showline=True,
                                                linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig_responded_category.update_layout(barmode='stack', title='KPI Monitoring(Responded) vs Trade Category',
                                                 plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig_responded_category, use_container_width=True)

        st.markdown('##')
        st.markdown('##')
        st.markdown(html_card_subheader_KPI_Recovered, unsafe_allow_html=True)
        st.markdown('##')
        st.markdown('Recovery Time refers to the time the fault or emergency was reported to the time the Contractor completed the work with evidence')
        st.markdown('##')

        x_KPI_building_010_recovered = df3.groupby(by='KPI_For_Recovered').Building_Trade.value_counts().loc['0-1hr'].index
        x_KPI_building_1030_recovered = df3.groupby(by='KPI_For_Recovered').Building_Trade.value_counts().loc['1-4hrs'].index
        x_KPI_building_3060_recovered = df3.groupby(by='KPI_For_Recovered').Building_Trade.value_counts().loc['4-8hrs'].index
        x_KPI_building_60inf_recovered = df3.groupby(by='KPI_For_Recovered').Building_Trade.value_counts().loc['8-np.inf'].index

        y_KPI_building_010_recovered = df3.groupby(by='KPI_For_Recovered').Building_Trade.value_counts().loc['0-1hr'].values
        y_KPI_building_1030_recovered = df3.groupby(by='KPI_For_Recovered').Building_Trade.value_counts().loc['1-4hrs'].values
        y_KPI_building_3060_recovered = df3.groupby(by='KPI_For_Recovered').Building_Trade.value_counts().loc['4-8hrs'].values
        y_KPI_building_60inf_recovered = df3.groupby(by='KPI_For_Recovered').Building_Trade.value_counts().loc['8-np.inf'].values

        x_KPI_category_010_recovered = df3.groupby(by='KPI_For_Recovered').Trade_Category.value_counts().loc['0-1hr'].index
        x_KPI_category_1030_recovered = df3.groupby(by='KPI_For_Recovered').Trade_Category.value_counts().loc['1-4hrs'].index
        x_KPI_category_3060_recovered = df3.groupby(by='KPI_For_Recovered').Trade_Category.value_counts().loc['4-8hrs'].index
        x_KPI_category_60inf_recovered = df3.groupby(by='KPI_For_Recovered').Trade_Category.value_counts().loc['8-np.inf'].index

        y_KPI_category_010_recovered = df3.groupby(by='KPI_For_Recovered').Trade_Category.value_counts().loc['0-1hr'].values
        y_KPI_category_1030_recovered = df3.groupby(by='KPI_For_Recovered').Trade_Category.value_counts().loc['1-4hrs'].values
        y_KPI_category_3060_recovered = df3.groupby(by='KPI_For_Recovered').Trade_Category.value_counts().loc['4-8hrs'].values
        y_KPI_category_60inf_recovered = df3.groupby(by='KPI_For_Recovered').Trade_Category.value_counts().loc['8-np.inf'].values

        fig_recovered_building, fig_recovered_category = st.columns([1, 2])
        with fig_recovered_building, _lock:
            fig_recovered_building = go.Figure(data=[
                go.Bar(name='0-1hr', x=x_KPI_building_010_recovered, y=y_KPI_building_010_recovered, marker_color=colorstackbarpass),
                go.Bar(name='1-4hrs', x=x_KPI_building_1030_recovered, y=y_KPI_building_1030_recovered, marker_color=colorstackbarfail01),
                go.Bar(name='4-8hrs', x=x_KPI_building_3060_recovered, y=y_KPI_building_3060_recovered, marker_color=colorstackbarfail02),
                go.Bar(name='8-np.inf', x=x_KPI_building_60inf_recovered, y=y_KPI_building_60inf_recovered, marker_color=colorstackbarfail03)
            ])
            fig_recovered_building.update_xaxes(title_text="Building Trade", tickangle=-45, title_font_color=titlefontcolor,
                                                showgrid=False, gridwidth=gridwidth, gridcolor=gridcolor, showline=True,
                                                linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig_recovered_building.update_yaxes(title_text='Number of Fault', title_font_color=titlefontcolor, showgrid=True,
                                                gridwidth=gridwidth, gridcolor=gridcolor, showline=True,
                                                linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig_recovered_building.update_layout(barmode='stack', title='KPI Monitoring(Recovered) vs Building Trade', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig_recovered_building, use_container_width=True)

        with fig_recovered_category, _lock:
            fig_recovered_category = go.Figure(data=[
                go.Bar(name='0-1hr', x=x_KPI_category_010_recovered, y=y_KPI_category_010_recovered, marker_color=colorstackbarpass),
                go.Bar(name='1-4hrs', x=x_KPI_category_1030_recovered, y=y_KPI_category_1030_recovered, marker_color=colorstackbarfail01),
                go.Bar(name='4-8hrs', x=x_KPI_category_3060_recovered, y=y_KPI_category_3060_recovered, marker_color=colorstackbarfail02),
                go.Bar(name='8-np.inf', x=x_KPI_category_60inf_recovered, y=y_KPI_category_60inf_recovered, marker_color=colorstackbarfail03)
            ])
            fig_recovered_category.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color=titlefontcolor,
                                                showgrid=False, gridwidth=gridwidth, gridcolor=gridcolor, showline=True,
                                                linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig_recovered_category.update_yaxes(title_text='Number of Fault', title_font_color=titlefontcolor, showgrid=True,
                                                gridwidth=gridwidth, gridcolor=gridcolor, showline=True,
                                                linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig_recovered_category.update_layout(barmode='stack', title='KPI Monitoring(Recovered) vs Trade Category', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig_recovered_category, use_container_width=True)


        # ---------------------------Fault vs Building Trade & Trade Category & Type of Fault------------------------

        st.markdown('##')
        st.markdown('##')
        st.markdown(html_card_subheader_Tier1, unsafe_allow_html=True)
        st.markdown('##')

        df3['Time_Acknowledged_hrs'] = df3.Time_Acknowledged_mins/60
        df3['Time_Site_Reached_hrs'] = df3.Time_Site_Reached_mins/60
        df3['Time_Work_Started_hrs'] = df3.Time_Work_Started_mins/60
        df3['Time_Work_Recovered_hrs'] = df3.Time_Work_Recovered_mins/60

        df4 = df3.loc[:, ['Site', 'Building', 'Level', 'Room', 'Building_Trade', 'Trade_Category', 'Type_of_Fault',
                          'Time_Acknowledged_hrs', 'Time_Site_Reached_hrs', 'Time_Work_Started_hrs',
                          'Time_Work_Recovered_hrs']]
        df4 = df4[['Site', 'Building', 'Level', 'Room', 'Building_Trade', 'Trade_Category', 'Type_of_Fault',
                   'Time_Acknowledged_hrs',
                   'Time_Site_Reached_hrs', 'Time_Work_Started_hrs', 'Time_Work_Recovered_hrs']]

        df5 = df4.groupby(by=['Building_Trade']).agg(['count', 'max', 'min', 'mean', 'sum']).sort_values(
            ('Time_Acknowledged_hrs', 'count'), ascending=False)
        cols_name = ['Fault_Acknowledged_count', 'Fault_Acknowledged_max(hrs)', 'Fault_Acknowledged_min(hrs)',
                     'Fault_Acknowledged_mean(hrs)',
                     'Fault_Acknowledged_sum(hrs)', 'Fault_Site_Reached_count', 'Fault_Site_Reached_max(hrs)',
                     'Fault_Site_Reached_min(hrs)',
                     'Fault_Site_Reached_mean(hrs)', 'Fault_Site_Reached_sum(hrs)', 'Fault_Work_Started_count',
                     'Fault_Work_Started_max(hrs)',
                     'Fault_Work_Started_min(hrs)', 'Fault_Work_Started_mean(hrs)', 'Fault_Work_Started_sum(hrs)',
                     'Fault_Recovered_count',
                     'Fault_Recovered_max(hrs)', 'Fault_Recovered_min(hrs)', 'Fault_Recovered_mean(hrs)',
                     'Fault_Recovered_sum(hrs)']
        df5.columns = cols_name
        df6 = df5.loc[:, ['Fault_Site_Reached_count', 'Fault_Site_Reached_mean(hrs)', 'Fault_Site_Reached_sum(hrs)',
                          'Fault_Recovered_count', 'Fault_Recovered_mean(hrs)', 'Fault_Recovered_sum(hrs)']]
        df6.reset_index(inplace=True)

        x = df6['Building_Trade']
        y4 = df6.Fault_Recovered_count
        y5 = df6['Fault_Recovered_mean(hrs)']
        y6 = df6['Fault_Recovered_sum(hrs)']

        fig04, fig05, fig06 = st.columns(3)
        with fig04, _lock:
            fig04 = go.Figure(data=[go.Pie(values=y4, labels=x, hoverinfo='all', textinfo='label+percent+value',
                                           textfont_size=15, textfont_color='white', textposition='inside',
                                           showlegend=False, hole=.4)])
            fig04.update_layout(title='Proportions of Building Trade(Recovered)', annotations=[
                dict(text='Recovered', x=0.5, y=0.5, font_color='white', font_size=15, showarrow=False)])
            fig04.update_traces(marker=dict(colors=colorpierecoveredtier1))
            st.plotly_chart(fig04, use_container_width=True)

        with fig05, _lock:
            fig05 = go.Figure(data=[
                go.Bar(x=x, y=y5, orientation='v', text=y5, textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                       textposition='auto', textangle=-45, texttemplate='%{text:.2f}')])
            fig05.update_xaxes(title_text="Building Trade", tickangle=-45, title_font_color=titlefontcolor, showgrid=False,
                               gridwidth=gridwidth, gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis,
                               linecolor=linecolor_xy_axis)
            fig05.update_yaxes(title_text='Mean Time Spent', title_font_color=titlefontcolor, showgrid=True,
                               gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig05.update_traces(marker_color=markercolor, marker_line_color=markerlinecolor,
                                marker_line_width=markerlinewidth, opacity=opacity02)
            fig05.update_layout(title='Mean Time Spent to Recovered(hrs)', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig05, use_container_width=True)

        with fig06, _lock:
            fig06 = go.Figure(data=[go.Bar(x=x, y=y6, orientation='v', text=y6,
                                           textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                           textposition='auto', textangle=-45, texttemplate='%{text:.2f}')
                                    ])
            fig06.update_xaxes(title_text="Building Trade", tickangle=-45, title_font_color=titlefontcolor, showgrid=False,
                               gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig06.update_yaxes(title_text='Total Time Spent', title_font_color=titlefontcolor, showgrid=True,
                               gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig06.update_traces(marker_color=markercolor, marker_line_color=markerlinecolor,
                                marker_line_width=markerlinewidth, opacity=opacity03)
            fig06.update_layout(title='Total Time Spent to Recovered(hrs)', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig06, use_container_width=True)

        st.markdown('##')
        st.markdown('##')
        st.markdown(html_card_subheader_Tier2, unsafe_allow_html=True)
        st.markdown('##')

        df7 = df4.groupby(by=['Trade_Category']).agg(['count', 'max', 'min', 'mean', 'sum']).sort_values(
            ('Time_Acknowledged_hrs', 'count'), ascending=False)
        cols_name01 = ['Fault_Acknowledged_count', 'Fault_Acknowledged_max(hrs)', 'Fault_Acknowledged_min(hrs)',
                       'Fault_Acknowledged_mean(hrs)',
                       'Fault_Acknowledged_sum(hrs)', 'Fault_Site_Reached_count', 'Fault_Site_Reached_max(hrs)',
                       'Fault_Site_Reached_min(hrs)',
                       'Fault_Site_Reached_mean(hrs)', 'Fault_Site_Reached_sum(hrs)', 'Fault_Work_Started_count',
                       'Fault_Work_Started_max(hrs)',
                       'Fault_Work_Started_min(hrs)', 'Fault_Work_Started_mean(hrs)', 'Fault_Work_Started_sum(hrs)',
                       'Fault_Recovered_count',
                       'Fault_Recovered_max(hrs)', 'Fault_Recovered_min(hrs)', 'Fault_Recovered_mean(hrs)',
                       'Fault_Recovered_sum(hrs)']
        df7.columns = cols_name01
        df8 = df7.loc[:, ['Fault_Site_Reached_count', 'Fault_Site_Reached_mean(hrs)', 'Fault_Site_Reached_sum(hrs)',
                          'Fault_Recovered_count', 'Fault_Recovered_mean(hrs)', 'Fault_Recovered_sum(hrs)']]
        df8.reset_index(inplace=True)

        df_fig10 = df8.loc[:, ['Trade_Category', 'Fault_Recovered_count']].sort_values('Fault_Recovered_count',
                                                                                       ascending=False).head(10)
        df_fig11 = df8.loc[:, ['Trade_Category', 'Fault_Recovered_mean(hrs)']].sort_values('Fault_Recovered_mean(hrs)',
                                                                                           ascending=False).head(10)
        df_fig12 = df8.loc[:, ['Trade_Category', 'Fault_Recovered_sum(hrs)']].sort_values('Fault_Recovered_sum(hrs)',
                                                                                          ascending=False).head(10)

        x_fig10 = df_fig10.Trade_Category
        y_fig10 = df_fig10['Fault_Recovered_count']
        x_fig11 = df_fig11.Trade_Category
        y_fig11 = df_fig11['Fault_Recovered_mean(hrs)']
        x_fig12 = df_fig12.Trade_Category
        y_fig12 = df_fig12['Fault_Recovered_sum(hrs)']

        fig10, fig11, fig12 = st.columns(3)
        with fig10, _lock:
            fig10 = go.Figure(data=[go.Bar(x=x_fig10, y=y_fig10, orientation='v', text=y_fig10,
                                           textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                           textposition='auto', textangle=-45)])
            fig10.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color=titlefontcolor, showgrid=False,
                               gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig10.update_yaxes(title_text='Count(Recovered)', title_font_color=titlefontcolor, showgrid=True,
                               gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig10.update_traces(marker_color=markercolor, marker_line_color=markerlinecolor,
                                marker_line_width=markerlinewidth, opacity=opacity01)
            fig10.update_layout(title='Count(Recovered)-Top 10', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig10, use_container_width=True)

        with fig11, _lock:
            fig11 = go.Figure(data=[go.Bar(x=x_fig11, y=y_fig11, orientation='v', text=y_fig11,
                                           textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                           textposition='auto', textangle=-45, texttemplate='%{text:.2f}')
                                    ])
            fig11.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color=titlefontcolor, showgrid=False,
                               gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig11.update_yaxes(title_text='Mean Time Spent', title_font_color=titlefontcolor, showgrid=True,
                               gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig11.update_traces(marker_color=markercolor, marker_line_color=markerlinecolor,
                                marker_line_width=markerlinewidth, opacity=opacity02)
            fig11.update_layout(title='Mean Time Spent to Recovered(hrs)-Top 10', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig11, use_container_width=True)

        with fig12, _lock:
            fig12 = go.Figure(data=[go.Bar(x=x_fig12, y=y_fig12, orientation='v', text=y_fig12,
                                           textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                           textposition='auto', textangle=-45, texttemplate='%{text:.2f}')
                                    ])
            fig12.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color=titlefontcolor, showgrid=False,
                               gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig12.update_yaxes(title_text='Total Time Spent', title_font_color=titlefontcolor, showgrid=True,
                               gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig12.update_traces(marker_color=markercolor, marker_line_color=markerlinecolor,
                                marker_line_width=markerlinewidth, opacity=opacity03)
            fig12.update_layout(title='Total Time Spent to Recovered(hrs)-Top 10', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig12, use_container_width=True)

        st.markdown('##')
        st.markdown('##')
        st.markdown(html_card_subheader_Tier3, unsafe_allow_html=True)
        st.markdown('##')

        df9 = df4.groupby(by=['Type_of_Fault']).agg(['count', 'max', 'min', 'mean', 'sum']).sort_values(
            ('Time_Acknowledged_hrs', 'count'), ascending=False)
        cols_name02 = ['Fault_Acknowledged_count', 'Fault_Acknowledged_max(hrs)', 'Fault_Acknowledged_min(hrs)',
                       'Fault_Acknowledged_mean(hrs)',
                       'Fault_Acknowledged_sum(hrs)', 'Fault_Site_Reached_count', 'Fault_Site_Reached_max(hrs)',
                       'Fault_Site_Reached_min(hrs)',
                       'Fault_Site_Reached_mean(hrs)', 'Fault_Site_Reached_sum(hrs)', 'Fault_Work_Started_count',
                       'Fault_Work_Started_max(hrs)',
                       'Fault_Work_Started_min(hrs)', 'Fault_Work_Started_mean(hrs)', 'Fault_Work_Started_sum(hrs)',
                       'Fault_Recovered_count',
                       'Fault_Recovered_max(hrs)', 'Fault_Recovered_min(hrs)', 'Fault_Recovered_mean(hrs)',
                       'Fault_Recovered_sum(hrs)']
        df9.columns = cols_name02
        df10 = df9.loc[:, ['Fault_Site_Reached_count', 'Fault_Site_Reached_mean(hrs)', 'Fault_Site_Reached_sum(hrs)',
                           'Fault_Recovered_count', 'Fault_Recovered_mean(hrs)', 'Fault_Recovered_sum(hrs)']]
        df10.reset_index(inplace=True)

        df_fig16 = df10.loc[:, ['Type_of_Fault', 'Fault_Recovered_count']].sort_values('Fault_Recovered_count',
                                                                                       ascending=False).head(10)
        df_fig17 = df10.loc[:, ['Type_of_Fault', 'Fault_Recovered_mean(hrs)']].sort_values('Fault_Recovered_mean(hrs)',
                                                                                           ascending=False).head(10)
        df_fig18 = df10.loc[:, ['Type_of_Fault', 'Fault_Recovered_sum(hrs)']].sort_values('Fault_Recovered_sum(hrs)',
                                                                                          ascending=False).head(10)

        x_fig16 = df_fig16.Type_of_Fault
        y_fig16 = df_fig16['Fault_Recovered_count']
        x_fig17 = df_fig17.Type_of_Fault
        y_fig17 = df_fig17['Fault_Recovered_mean(hrs)']
        x_fig18 = df_fig18.Type_of_Fault
        y_fig18 = df_fig18['Fault_Recovered_sum(hrs)']

        fig16, fig17, fig18 = st.columns(3)
        with fig16, _lock:
            fig16 = go.Figure(data=[go.Bar(x=x_fig16, y=y_fig16, orientation='v', text=y_fig16,
                                           textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                           textposition='auto', textangle=-45)])
            fig16.update_xaxes(title_text="Type of Fault", tickangle=-45, title_font_color=titlefontcolor, showgrid=False,
                               gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig16.update_yaxes(title_text='Count(Recovered)', title_font_color=titlefontcolor, showgrid=True,
                               gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig16.update_traces(marker_color=markercolor, marker_line_color=markerlinecolor,
                                marker_line_width=markerlinewidth, opacity=opacity01)
            fig16.update_layout(title='Count(Recovered)-Top 10', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig16, use_container_width=True)

        with fig17, _lock:
            fig17 = go.Figure(data=[go.Bar(x=x_fig17, y=y_fig17, orientation='v', text=y_fig17,
                                           textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                           textposition='auto', textangle=-45, texttemplate='%{text:.2f}')])
            fig17.update_xaxes(title_text="Type of Fault", tickangle=-45, title_font_color=titlefontcolor, showgrid=False,
                               gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig17.update_yaxes(title_text='Mean Time Spent', title_font_color=titlefontcolor, showgrid=True,
                               gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig17.update_traces(marker_color=markercolor, marker_line_color=markerlinecolor,
                                marker_line_width=markerlinewidth, opacity=opacity02)
            fig17.update_layout(title='Mean Time Spent to Recovered(hrs)-Top 10', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig17, use_container_width=True)

        with fig18, _lock:
            fig18 = go.Figure(data=[go.Bar(x=x_fig18, y=y_fig18, orientation='v', text=y_fig18,
                                           textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                           textposition='auto', textangle=-45, texttemplate='%{text:.2f}')
                                    ])
            fig18.update_xaxes(title_text="Type of Fault", tickangle=-45, title_font_color=titlefontcolor, showgrid=False,
                               gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig18.update_yaxes(title_text='Total Time Spent', title_font_color=titlefontcolor, showgrid=True,
                               gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig18.update_traces(marker_color=markercolor, marker_line_color=markerlinecolor,
                                marker_line_width=markerlinewidth, opacity=opacity03)
            fig18.update_layout(title='Total Time Spent to Recovered(hrs)-Top 10', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig18, use_container_width=True)

     #-------------------------------------------Fault vs Location-------------------------------------------------

        st.markdown('##')
        st.markdown('##')
        st.markdown(html_card_subheader_location, unsafe_allow_html=True)
        st.markdown('##')

        ## groupby building
        df11 = df4.groupby(by=['Building']).agg(['count', 'max', 'min', 'mean', 'sum'])
        cols_name_building = ['Fault_Acknowledged_count', 'Fault_Acknowledged_max(hrs)', 'Fault_Acknowledged_min(hrs)', 'Fault_Acknowledged_mean(hrs)',
                       'Fault_Acknowledged_sum(hrs)', 'Fault_Site_Reached_count', 'Fault_Site_Reached_max(hrs)', 'Fault_Site_Reached_min(hrs)',
                       'Fault_Site_Reached_mean(hrs)', 'Fault_Site_Reached_sum(hrs)', 'Fault_Work_Started_count', 'Fault_Work_Started_max(hrs)',
                       'Fault_Work_Started_min(hrs)', 'Fault_Work_Started_mean(hrs)', 'Fault_Work_Started_sum(hrs)', 'Fault_Recovered_count',
                       'Fault_Recovered_max(hrs)', 'Fault_Recovered_min(hrs)', 'Fault_Recovered_mean(hrs)', 'Fault_Recovered_sum(hrs)']
        df11.columns = cols_name_building
        df12 = df11.loc[:, ['Fault_Recovered_count', 'Fault_Recovered_sum(hrs)']]

        x_fig19 = df12['Fault_Recovered_count'].sort_values().index
        y_fig19 = df12['Fault_Recovered_count'].sort_values().values

        x_fig20 = df12['Fault_Recovered_sum(hrs)'].sort_values().index
        y_fig20 = df12['Fault_Recovered_sum(hrs)'].sort_values().values


        fig19, fig20 = st.columns(2)
        with fig19, _lock:
            fig19 = go.Figure(data=[go.Bar(x=y_fig19, y=x_fig19, orientation='h', text=y_fig19,
                                 textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                 textposition='auto', textangle=0)
                                    ])
            fig19.update_xaxes(title_text="Number of Fault", title_font_color=titlefontcolor, showgrid=True, gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig19.update_yaxes(title_text='Building', title_font_color=titlefontcolor, showgrid=False, gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis, tickmode='linear')
            fig19.update_traces(marker_color=markercolor, marker_line_color=markerlinecolor, marker_line_width=markerlinewidth, opacity=opacity02)
            fig19.update_layout(title='Number of Fault vs Building', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig19, use_container_width=True)

        with fig20, _lock:
            fig20 = go.Figure(data=[go.Bar(x=y_fig20, y=x_fig20, orientation='h', text=y_fig20,
                                   textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                   textposition='auto', textangle=0, texttemplate='%{text:.2f}')
                                    ])
            fig20.update_xaxes(title_text="Total Time Spent", title_font_color=titlefontcolor, showgrid=True, gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig20.update_yaxes(title_text='Building', title_font_color=titlefontcolor, showgrid=False, gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis, tickmode='linear')
            fig20.update_traces(marker_color=markercolor, marker_line_color=markerlinecolor, marker_line_width=markerlinewidth, opacity=opacity03)
            fig20.update_layout(title='Total Time Spent(hrs) vs Building', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig20, use_container_width=True)

    ## groupby building level
        df4['buildinglevel'] = df4.Building + '-' + df4.Level
        df13 = df4.groupby(by=['buildinglevel']).agg(['count', 'max', 'min', 'mean', 'sum'])
        cols_name_buildinglevel = ['Fault_Acknowledged_count', 'Fault_Acknowledged_max(hrs)', 'Fault_Acknowledged_min(hrs)', 'Fault_Acknowledged_mean(hrs)',
                       'Fault_Acknowledged_sum(hrs)', 'Fault_Site_Reached_count', 'Fault_Site_Reached_max(hrs)', 'Fault_Site_Reached_min(hrs)',
                       'Fault_Site_Reached_mean(hrs)', 'Fault_Site_Reached_sum(hrs)', 'Fault_Work_Started_count', 'Fault_Work_Started_max(hrs)',
                       'Fault_Work_Started_min(hrs)', 'Fault_Work_Started_mean(hrs)', 'Fault_Work_Started_sum(hrs)', 'Fault_Recovered_count',
                       'Fault_Recovered_max(hrs)', 'Fault_Recovered_min(hrs)', 'Fault_Recovered_mean(hrs)', 'Fault_Recovered_sum(hrs)']
        df13.columns = cols_name_buildinglevel
        df14 = df13.loc[:, ['Fault_Recovered_count', 'Fault_Recovered_sum(hrs)']]

        x_fig21 = df14['Fault_Recovered_count'].sort_values().index
        y_fig21 = df14['Fault_Recovered_count'].sort_values().values

        x_fig22 = df14['Fault_Recovered_sum(hrs)'].sort_values().index
        y_fig22 = df14['Fault_Recovered_sum(hrs)'].sort_values().values


        fig21, fig22 = st.columns(2)
        with fig21, _lock:
            fig21 = go.Figure(data=[go.Bar(x=y_fig21, y=x_fig21, orientation='h', text=y_fig21,
                                 textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                 textposition='auto', textangle=0)
                                    ])
            fig21.update_xaxes(title_text="Number of Fault", title_font_color=titlefontcolor, showgrid=True,
                               gridwidth=gridwidth, gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig21.update_yaxes(title_text='Level', title_font_color=titlefontcolor, showgrid=False, gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis, tickmode='linear')
            fig21.update_traces(marker_color=markercolor, marker_line_color=markerlinecolor, marker_line_width=markerlinewidth, opacity=opacity02)
            fig21.update_layout(title='Number of Fault vs Building& Level', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig21, use_container_width=True)

        with fig22, _lock:
            fig22 = go.Figure(data=[go.Bar(x=y_fig22, y=x_fig22, orientation='h', text=y_fig22,
                                   textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                   textposition='auto', textangle=0, texttemplate='%{text:.2f}')
                                    ])
            fig22.update_xaxes(title_text="Total Time Spent", title_font_color=titlefontcolor, showgrid=True, gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig22.update_yaxes(title_text='Level', title_font_color=titlefontcolor, showgrid=False, gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis, tickmode='linear')
            fig22.update_traces(marker_color=markercolor, marker_line_color=markerlinecolor, marker_line_width=markerlinewidth, opacity=opacity03)
            fig22.update_layout(title='Total Time Spent(hrs) vs Building& Level', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig22, use_container_width=True)


    ## groupby building level room
        df4['buildinglevelroom'] = df4.Building + '-' + df4.Level + '-' + df4.Room
        df15 = df4.groupby(by=['buildinglevelroom']).agg(['count', 'max', 'min', 'mean', 'sum'])
        cols_name_buildinglevelroom = ['Fault_Acknowledged_count', 'Fault_Acknowledged_max(hrs)', 'Fault_Acknowledged_min(hrs)', 'Fault_Acknowledged_mean(hrs)',
                       'Fault_Acknowledged_sum(hrs)', 'Fault_Site_Reached_count', 'Fault_Site_Reached_max(hrs)', 'Fault_Site_Reached_min(hrs)',
                       'Fault_Site_Reached_mean(hrs)', 'Fault_Site_Reached_sum(hrs)', 'Fault_Work_Started_count', 'Fault_Work_Started_max(hrs)',
                       'Fault_Work_Started_min(hrs)', 'Fault_Work_Started_mean(hrs)', 'Fault_Work_Started_sum(hrs)', 'Fault_Recovered_count',
                       'Fault_Recovered_max(hrs)', 'Fault_Recovered_min(hrs)', 'Fault_Recovered_mean(hrs)', 'Fault_Recovered_sum(hrs)']
        df15.columns = cols_name_buildinglevelroom

        df16 = df15.loc[:, ['Fault_Recovered_count', 'Fault_Recovered_sum(hrs)']].sort_values('Fault_Recovered_count', ascending=False).head(20)
        df17 = df15.loc[:, ['Fault_Recovered_count', 'Fault_Recovered_sum(hrs)']].sort_values('Fault_Recovered_sum(hrs)',ascending=False).head(20)

        x_fig23 = df16['Fault_Recovered_count'].sort_values().index
        y_fig23 = df16['Fault_Recovered_count'].sort_values().values

        x_fig24 = df17['Fault_Recovered_sum(hrs)'].sort_values().index
        y_fig24 = df17['Fault_Recovered_sum(hrs)'].sort_values().values


        fig23, fig24 = st.columns(2)
        with fig23, _lock:
            fig23 = go.Figure(data=[go.Bar(x=y_fig23, y=x_fig23, orientation='h', text=y_fig23,
                                 textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                 textposition='auto', textangle=0)
                                    ])
            fig23.update_xaxes(title_text="Number of Fault", title_font_color=titlefontcolor, showgrid=True,
                               gridwidth=gridwidth, gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig23.update_yaxes(title_text='Room', title_font_color=titlefontcolor, showgrid=False, gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis, tickmode='linear')
            fig23.update_traces(marker_color=markercolor, marker_line_color=markerlinecolor, marker_line_width=markerlinewidth, opacity=opacity02)
            fig23.update_layout(title='Number of Fault vs Building Floor& Room-Top 20', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig23, use_container_width=True)

        with fig24, _lock:
            fig24 = go.Figure(data=[go.Bar(x=y_fig24, y=x_fig24, orientation='h', text=y_fig24,
                                   textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                   textposition='auto', textangle=0, texttemplate='%{text:.1f}')
                                    ])
            fig24.update_xaxes(title_text="Total Time Spent", title_font_color=titlefontcolor, showgrid=True, gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis)
            fig24.update_yaxes(title_text='Room', title_font_color=titlefontcolor, showgrid=False, gridwidth=gridwidth,
                               gridcolor=gridcolor, showline=True, linewidth=linewidth_xy_axis, linecolor=linecolor_xy_axis, tickmode='linear')
            fig24.update_traces(marker_color=markercolor, marker_line_color=markerlinecolor, marker_line_width=markerlinewidth, opacity=opacity03)
            fig24.update_layout(title='Total Time Spent(hrs) vs Building Floor& Room-Top 20', plot_bgcolor=plot_bgcolor)
            st.plotly_chart(fig24, use_container_width=True)





    # --------------------------------------Schedule----------------------------------------------------------------------
    if page =='Schedules':
        def fetch_file_schedules(filename):
            cols = ['Schedule ID', 'Building Trade', 'Trade Category', 'Strategic Partner',
               'Frequency', 'Description', 'Type', 'Scope', 'Site', 'Building',
               'Floor', 'Room', 'Start Date',
               'End Date', 'Work Started Date', 'Work Completed Date',
               'Attended By', 'Portal ID', 'Service Report Completed Date',
               'Total Number of Service Reports',
               'Total Number of Quantity in Service Reports', 'Asset Tag Number',
               'Alert Case']
            parse_dates = ['Start Date', 'End Date', 'Work Started Date', 'Work Completed Date',
                           'Service Report Completed Date']
            return pd.read_excel(filename, header=0, index_col='Schedule ID', usecols=cols, parse_dates=parse_dates)

        dfs = fetch_file_schedules('schedules.xlsx')
        dfs.columns = dfs.columns.str.replace(' ', '_')
        dfs['Time_Work_Completed_hrs'] = (dfs.Work_Completed_Date - dfs.Work_Started_Date) / pd.Timedelta(hours=1)

    # ----------------------------------------Sidebar---------------------------------------------------------------------
        st.sidebar.header('Please Filter Here:')

        Building_Trade = st.sidebar.multiselect(
            'Select the Building Trade:',
            options=dfs['Building_Trade'].unique(),
            default=dfs['Building_Trade'].unique()
        )

        Trade_Category = st.sidebar.multiselect(
            'Select the Trade Category:',
            options=dfs['Trade_Category'].unique(),
            default=dfs['Trade_Category'].unique()
        )

        dfs = dfs.query(
            'Building_Trade ==@Building_Trade & Trade_Category==@Trade_Category'
        )
     # ----------------------------------------Main page-----------------------------------------------------------
        html_card_title_schedules="""
        <div class="card">
          <div class="card-body" style="border-radius: 10px 10px 0px 0px; padding-top: 5px; width: 800px;
           height: 50px;">
            <h1 class="card-title" style=color:#1dacd6; font-family:Georgia; text-align: left; padding: 0px 0;">SCHEDULES DASHBOARD Nov 2021</h1>
          </div>
        </div>
        """
        st.markdown(html_card_title_schedules, unsafe_allow_html=True)
        st.markdown('##')
        st.markdown('##')

        total_schedule = dfs.shape[0]
        schedule_outstanding = dfs[dfs['Work_Completed_Date'].isna()].shape[0]
        schedule_completed = dfs[dfs['Work_Completed_Date'].notna()].shape[0]
        total_SR = dfs.Total_Number_of_Service_Reports.sum()
        # total_asset =
        alert_case = int(dfs['Alert_Case'].sum())

        column01_schedule, column02_schedule, column03_schedule, column04_schedule, column05_schedule = st.columns(5)
        with column01_schedule, _lock:
            st.markdown(f"<h6 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:bottom; color: #1dacd6;'>Total</h6>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:top; color: #1dacd6;'>{total_schedule}</h2>", unsafe_allow_html=True)

        with column02_schedule, _lock:
            st.markdown(f"<h6 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:bottom; color: #1dacd6;'>Outstanding</h6>",unsafe_allow_html=True)
            st.markdown(f"<h2 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:top; color: #1dacd6;'>{schedule_outstanding}</h2>", unsafe_allow_html=True)

        with column03_schedule, _lock:
            st.markdown(f"<h6 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:bottom; color: #1dacd6;'>Completed</h6>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:top; color: #1dacd6;'>{schedule_completed}</h2>", unsafe_allow_html=True)

        with column04_schedule, _lock:
            st.markdown(f"<h6 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:bottom; color: #1dacd6;'>Alert</h6>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:top; color: red;'>{alert_case}</h2>", unsafe_allow_html=True)

        with column05_schedule, _lock:
            st.markdown(f"<h6 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:bottom; color: #1dacd6;'>No.of SR</h6>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='background-color:#0e1117; width:120px; height:20px; text-align: left; vertical-align:top; color: #1dacd6;'>{total_SR}</h2>", unsafe_allow_html=True)

        html_card_subheader_outstanding_schedules="""
        <div class="card">
          <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #1dacd6; padding-top: 5px; width: 350px;
           height: 50px;">
            <h3 class="card-title" style="background-color:#1dacd6; color:#eabd1d; font-family:Georgia; text-align: center; padding: 0px 0;">Outstanding Schedules</h3>
          </div>
        </div>
        """
        html_card_subheader_daily_schedules="""
        <div class="card">
          <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #1dacd6; padding-top: 5px; width: 350px;
           height: 50px;">
            <h3 class="card-title" style="background-color:#1dacd6; color:#eabd1d; font-family:Georgia; text-align: center; padding: 0px 0;">Daily Schedule Cases</h3>
          </div>
        </div>
        """
        html_card_subheader_schedules_Tier1="""
        <div class="card">
          <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #1dacd6; padding-top: 5px; width: 600px;
           height: 50px;">
            <h3 class="card-title" style="background-color:#1dacd6; color:#eabd1d; font-family:Georgia; text-align: center; padding: 0px 0;">Completed Schedules vs Building Trade</h3>
          </div>
        </div>
        """
        html_card_subheader_schedules_Tier2="""
        <div class="card">
          <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #1dacd6; padding-top: 5px; width: 600px;
           height: 50px;">
            <h3 class="card-title" style="background-color:#1dacd6; color:#eabd1d; font-family:Georgia; text-align: center; padding: 0px 0;">Completed Schedules vs Trade Category</h3>
          </div>
        </div>
        """

#--------------------------------------- color & width & opacity----------------------------------------------
        # Pie chart
        colorpieoutstandings = ['#1dacd6', '#4c9085', '#50a747', '#59656d', '#06c2ac', '#137e6d', '#929906', '#ff9408']
        colorpierecoveredstier1 = ['#1dacd6', '#4c9085', '#50a747', '#59656d', '#06c2ac', '#137e6d', '#929906', '#ff9408']

        # all barchart and linechart
        titlefontcolors = '#1dacd6'
        gridwidths = 0.1
        gridcolors = '#1f3b4d'
        plot_bgcolors = 'rgba(0,0,0,0)'

        # x&y axis width and color
        linewidths_xy_axis = 1
        linecolors_xy_axis = '#59656d'

        # all barchart
        markercolors = '#1dacd6'
        markerlinecolors = '#1dacd6'
        markerlinewidths = 1

        #linechart
        linecolors = '#1dacd6'
        linewidths = 2
#------------------------------------------ Outstanding Schedules-------------------------------------------------
        st.markdown('##')
        st.markdown('##')
        st.markdown("""<hr style="height:5px;border:none;color:#333;background-color:#333;" /> """,
                    unsafe_allow_html=True)
        st.markdown(html_card_subheader_outstanding_schedules, unsafe_allow_html=True)
        st.markdown('##')

        dfs_outstanding = dfs[dfs['Work_Completed_Date'].isna()]
        sers_outstanding_building = dfs_outstanding.groupby(['Building_Trade'])['Trade_Category'].count().sort_values(ascending=False)
        sers_outstanding_category = dfs_outstanding.groupby(['Trade_Category'])['Building_Trade'].count().sort_values(ascending=False)

        xs_outstanding_building = sers_outstanding_building.index
        ys_outstanding_building = sers_outstanding_building.values
        xs_outstanding_category = sers_outstanding_category.index
        ys_outstanding_category = sers_outstanding_category.values

        figs_outstanding_building, figs_outstanding_category = st.columns([1, 2])

        with figs_outstanding_building, _lock:
            figs_outstanding_building = go.Figure(data=[go.Pie(labels=xs_outstanding_building, values=ys_outstanding_building, hoverinfo='all', textinfo='label+percent+value',
                                                               textfont_size=15, textfont_color='white', textposition='inside', showlegend=False, hole=.4)])
            figs_outstanding_building.update_layout(title='Number of Schedule vs Building Trade', annotations=[dict(text='Outstanding', x=0.5, y=0.5, font_size=15, font_color='white', showarrow=False)])
            figs_outstanding_building.update_traces(marker=dict(colors=colorpieoutstandings))
            st.plotly_chart(figs_outstanding_building, use_container_width=True)

        with figs_outstanding_category, _lock:
            figs_outstanding_category = go.Figure(data=[go.Bar(x=xs_outstanding_category, y=ys_outstanding_category, orientation='v',
                                                               text=ys_outstanding_category,textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                                               textposition='auto', textangle=-45)
                                                        ])
            figs_outstanding_category.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color=titlefontcolors, showgrid=False, gridwidth=gridwidths,
                               gridcolor=gridcolors, showline=True, linewidth=linewidths_xy_axis, linecolor=linecolors_xy_axis)
            figs_outstanding_category.update_yaxes(title_text='Number of Schedule', title_font_color=titlefontcolors, showgrid=True, gridwidth=gridwidths,
                               gridcolor=gridcolors, showline=True, linewidth=linewidths_xy_axis, linecolor=linecolors_xy_axis)
            figs_outstanding_category.update_traces(marker_color=markercolors, marker_line_color=markerlinecolors, marker_line_width=markerlinewidths)
            figs_outstanding_category.update_layout(title='Number of Schedule vs Trade Category', plot_bgcolor=plot_bgcolors)
            st.plotly_chart(figs_outstanding_category, use_container_width=True)

# ------------------------------------------ Daily Schedules-------------------------------------------------
        st.markdown("""<hr style="height:5px;border:none;color:#333;background-color:#333;" /> """,
                    unsafe_allow_html=True)
        st.markdown(html_card_subheader_daily_schedules, unsafe_allow_html=True)
        st.markdown('##')

        dfs_completed = dfs[dfs['Work_Completed_Date'].notna()].loc[:, ['Building_Trade', 'Trade_Category', 'Strategic_Partner', 'Frequency',
               'Description', 'Type', 'Scope', 'Site', 'Building', 'Floor', 'Room',
               'Start_Date', 'End_Date', 'Work_Started_Date', 'Work_Completed_Date',
               'Attended_By', 'Service_Report_Completed_Date', 'Time_Work_Completed_hrs']]

        dfs_completedupdated = dfs_completed.loc[:, ['Building_Trade', 'Trade_Category', 'Work_Started_Date', 'Time_Work_Completed_hrs']]

        xs_daily = dfs_completedupdated['Work_Started_Date'].dt.day.value_counts().sort_index().index
        ys_daily = dfs_completedupdated['Work_Started_Date'].dt.day.value_counts().sort_index().values
        ys_mean = dfs_completedupdated['Work_Started_Date'].dt.day.value_counts().sort_index().mean()

        figs_daily = go.Figure(data=go.Scatter(x=xs_daily, y=ys_daily, mode='lines+markers+text', line=dict(color=linecolors, width=linewidths),
                                text=ys_daily, textfont=dict(family='sana serif', size=14, color='#c4fff7'), textposition='top center'))
        figs_daily.add_hline(y=ys_mean, line_dash='dot', line_color='#96ae8d', line_width=2, annotation_text='Average Line',
                                annotation_position='bottom right', annotation_font_size=18, annotation_font_color='green')
        figs_daily.update_xaxes(title_text='Date', tickangle=-45, title_font_color=titlefontcolors, tickmode='linear',
                                   range=[1, 31], showgrid=False, gridwidth=gridwidths, gridcolor=gridcolors,
                                showline=True, linewidth=linewidths_xy_axis, linecolor=linecolors_xy_axis)
        figs_daily.update_yaxes(title_text='Number of Schedule', title_font_color=titlefontcolors, tickmode='linear', showgrid=False,
                                gridwidth=gridwidths, gridcolor=gridcolors, showline=True, linewidth=linewidths_xy_axis, linecolor=linecolors_xy_axis)
        figs_daily.update_layout(title='Number of Schedule vs Date', plot_bgcolor=plot_bgcolors,
                                 # xaxis=dict(showticklabels=True, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
                                 # yaxis=dict(showticklabels=True, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)'))
                                 )
        st.plotly_chart(figs_daily, use_container_width=True)

# ------------------------------------------ Schedules Tier1 & Tier2-------------------------------------------------
        st.markdown('##')
        st.markdown('##')
        st.markdown(html_card_subheader_schedules_Tier1, unsafe_allow_html=True)
        st.markdown('##')

        dfs1 = dfs_completedupdated.groupby(by=['Building_Trade']).agg(['count', 'max', 'min', 'mean', 'sum']).sort_values(('Time_Work_Completed_hrs', 'count'), ascending=False)
        col_name_s1 = ['Schedule_Completed_count', 'Time_Schedule_Completed_max(hrs)', 'Time_Schedule_Completed_min(hrs)',
                       'Time_Schedule_Completed_mean(hrs)', 'Time_Schedule_Completed_sum(hrs)']
        dfs1.columns = col_name_s1

        dfs1.reset_index(inplace=True)

        xs1 = dfs1['Building_Trade']
        ys1 = dfs1['Schedule_Completed_count']
        ys2 = dfs1['Time_Schedule_Completed_mean(hrs)']
        ys3 = dfs1['Time_Schedule_Completed_sum(hrs)']

        figs01, figs02, figs03 = st.columns(3)
        with figs01, _lock:
            figs01 = go.Figure(data=[go.Pie(values=ys1, labels=xs1, hoverinfo='all', textinfo='label+percent+value', textfont_size=15, textfont_color='white', textposition='inside', showlegend=False, hole=.4)])
            figs01.update_layout(title='Proportions of Building Trade', annotations=[dict(text='Completed', x=0.5, y=0.5, font_size=15, font_color='white', showarrow=False)])
            figs01.update_traces(marker=dict(colors=colorpierecoveredstier1))
            st.plotly_chart(figs01, use_container_width=True)

        with figs02, _lock:
            figs02 = go.Figure(data=[go.Bar(x=xs1, y=ys2, orientation='v', text=ys2,
                                            textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                            textposition='auto', textangle=-45, texttemplate='%{text:.2f}')
                                     ])
            figs02.update_xaxes(title_text="Building Trade", tickangle=-45, title_font_color=titlefontcolors, showgrid=False, gridwidth=gridwidths,
                               gridcolor=gridcolors, showline=True, linewidth=linewidths_xy_axis, linecolor=linecolors_xy_axis)
            figs02.update_yaxes(title_text='Mean Time Spent(hrs)', title_font_color=titlefontcolors, showgrid=True, gridwidth=gridwidths,
                               gridcolor=gridcolors, showline=True, linewidth=linewidths_xy_axis, linecolor=linecolors_xy_axis)
            figs02.update_traces(marker_color=markercolors, marker_line_color=markerlinecolors, marker_line_width=markerlinewidths)
            figs02.update_layout(title='Mean Time Spent to Complete(hrs)', plot_bgcolor=plot_bgcolors)
            st.plotly_chart(figs02, use_container_width=True)

        with figs03, _lock:
            figs03 = go.Figure(data=[go.Bar(x=xs1, y=ys3, orientation='v', text=ys3,
                                            textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                            textposition='auto', textangle=-45, texttemplate='%{text:.2f}')
                                     ])
            figs03.update_xaxes(title_text="Building Trade", tickangle=-45, title_font_color=titlefontcolors, showgrid=False, gridwidth=gridwidths,
                               gridcolor=gridcolors, showline=True, linewidth=linewidths_xy_axis, linecolor=linecolors_xy_axis)
            figs03.update_yaxes(title_text='Total Time Spent(hrs)', title_font_color=titlefontcolors, showgrid=True, gridwidth=gridwidths,
                               gridcolor=gridcolors, showline=True, linewidth=linewidths_xy_axis, linecolor=linecolors_xy_axis)
            figs03.update_traces(marker_color=markercolors, marker_line_color=markerlinecolors, marker_line_width=markerlinewidths)
            figs03.update_layout(title='Total Time Spent to Complete(hrs)', plot_bgcolor=plot_bgcolors)
            st.plotly_chart(figs03, use_container_width=True)

        st.markdown('##')
        st.markdown('##')
        st.markdown(html_card_subheader_schedules_Tier2, unsafe_allow_html=True)
        st.markdown('##')

        dfs2 = dfs_completedupdated.groupby(by=['Trade_Category']).agg(['count', 'max', 'min', 'mean', 'sum'])
        col_name_s2 = ['Schedule_Completed_count', 'Time_Schedule_Completed_max(hrs)', 'Time_Schedule_Completed_min(hrs)', 'Time_Schedule_Completed_mean(hrs)', 'Time_Schedule_Completed_sum(hrs)']
        dfs2.columns = col_name_s2
        dfs2.reset_index(inplace=True)

        dfs_fig04 = dfs2.loc[:, ['Trade_Category', 'Schedule_Completed_count']].sort_values('Schedule_Completed_count', ascending=False).head(10)
        dfs_fig05 = dfs2.loc[:, ['Trade_Category', 'Time_Schedule_Completed_mean(hrs)']].sort_values('Time_Schedule_Completed_mean(hrs)', ascending=False).head(10)
        dfs_fig06 = dfs2.loc[:, ['Trade_Category', 'Time_Schedule_Completed_sum(hrs)']].sort_values('Time_Schedule_Completed_sum(hrs)', ascending=False).head(10)

        xs_fig04 = dfs_fig04['Trade_Category']
        ys_fig04 = dfs_fig04['Schedule_Completed_count']

        xs_fig05 = dfs_fig05['Trade_Category']
        ys_fig05 = dfs_fig05['Time_Schedule_Completed_mean(hrs)']

        xs_fig06 = dfs_fig06['Trade_Category']
        ys_fig06 = dfs_fig06['Time_Schedule_Completed_sum(hrs)']

        figs04, figs05, figs06 = st.columns(3)
        with figs04, _lock:
            figs04 = go.Figure(data=[go.Bar(x=xs_fig04, y=ys_fig04, orientation='v', text=ys_fig04,
                                            textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                            textposition='auto', textangle=-45)
                                     ])
            figs04.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color=titlefontcolors, showgrid=False,
                                gridwidth=gridwidths, gridcolor=gridcolors, showline=True, linewidth=linewidths_xy_axis, linecolor=linecolors_xy_axis)
            figs04.update_yaxes(title_text='Count', title_font_color=titlefontcolors, showgrid=True, gridwidth=gridwidths,
                               gridcolor=gridcolors, showline=True, linewidth=linewidths_xy_axis, linecolor=linecolors_xy_axis)
            figs04.update_traces(marker_color=markercolors, marker_line_color=markerlinecolors, marker_line_width=markerlinewidths)
            figs04.update_layout(title='Count-Top 10', plot_bgcolor=plot_bgcolors)
            st.plotly_chart(figs04, use_container_width=True)

        with figs05, _lock:
            figs05 = go.Figure(data=[go.Bar(x=xs_fig05, y=ys_fig05, orientation='v', text=ys_fig05,
                                            textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                            textposition='auto', textangle=-45, texttemplate='%{text:.2f}')
                                     ])
            figs05.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color=titlefontcolors, showgrid=False, gridwidth=gridwidths,
                               gridcolor=gridcolors, showline=True, linewidth=linewidths_xy_axis, linecolor=linecolors_xy_axis)
            figs05.update_yaxes(title_text='Mean Time Spent(hrs)', title_font_color=titlefontcolors, showgrid=True, gridwidth=gridwidths,
                               gridcolor=gridcolors, showline=True, linewidth=linewidths_xy_axis, linecolor=linecolors_xy_axis)
            figs05.update_traces(marker_color=markercolors, marker_line_color=markerlinecolors, marker_line_width=markerlinewidths)
            figs05.update_layout(title='Mean Time Spent to Complete(hrs)-Top 10', plot_bgcolor=plot_bgcolors)
            st.plotly_chart(figs05, use_container_width=True)

        with figs06, _lock:
            figs06 = go.Figure(data=[go.Bar(x=xs_fig06, y=ys_fig06, orientation='v', text=ys_fig06,
                                            textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                            textposition='auto', textangle=-45, texttemplate='%{text:.2f}')
                                     ])
            figs06.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color=titlefontcolors, showgrid=False, gridwidth=gridwidths,
                               gridcolor=gridcolors, showline=True, linewidth=linewidths_xy_axis, linecolor=linecolors_xy_axis)
            figs06.update_yaxes(title_text='Total Time Spent(hrs)', title_font_color=titlefontcolors, showgrid=True, gridwidth=gridwidths,
                               gridcolor=gridcolors, showline=True, linewidth=linewidths_xy_axis, linecolor=linecolors_xy_axis)
            figs06.update_traces(marker_color=markercolors, marker_line_color=markerlinecolors, marker_line_width=markerlinewidths)
            figs06.update_layout(title='Total Time Spent to Complete(hrs)-Top 10', plot_bgcolor=plot_bgcolors)
            st.plotly_chart(figs06, use_container_width=True)








    # --------------------------------------Inventories----------------------------------------------------------------------
    if page =='Inventories':
        use_cols =['Description', 'Category', 'Subcategory', 'Ref. ID', 'Reference Location', 'Quantity', 'Request to draw or add',
               'Reference number', 'Created date']
        date=['Created date']
        dfEC11 = pd.read_excel('Transaction 2021-12-04 012805(EC11).xlsx', header=1, usecols=use_cols, parse_dates=date)
        dfEC11['Created day'] = dfEC11['Created date'].dt.day

        dfCM18 = pd.read_excel('Transaction 2021-12-04 012805(CM18).xlsx', header=1, usecols=use_cols, parse_dates=date)
        dfCM18['Created day'] = dfCM18['Created date'].dt.day

        serEC11_daily = dfEC11.groupby(by=['Created day'])['Request to draw or add'].sum()

        serEC11fast = dfEC11.groupby(by=['Description'])['Request to draw or add'].sum().sort_values(ascending=True)

        html_card_title_inventories="""
            <div class="card">
              <div class="card-body" style="border-radius: 10px 10px 0px 0px; padding-top: 5px; width: 800px;
               height: 50px;">
                <h1 class="card-title" style=color:#ff4f00; font-family:Georgia; text-align: left; padding: 0px 0;">INVENTORIES MOVEMENT Nov 2021</h1>
              </div>
            </div>
            """
        st.markdown(html_card_title_inventories, unsafe_allow_html=True)
        st.markdown('##')
        st.markdown('##')
        st.subheader('GBB-EC11')

        total_inventory_balanceEC11 = dfEC11['Quantity'].sum()
        total_inventory_requestedEC11 = dfEC11['Request to draw or add'].sum()
        total_replenishmentEC11 = 0

        column01_inventory, column02_inventory, column03_inventory = st.columns(3)

        with column01_inventory, _lock:
            st.markdown('**Balance**')
            st.markdown(f"<h2 style='text-align: left; color: #703bef;'>{total_inventory_balanceEC11}</h2>", unsafe_allow_html=True)
        with column02_inventory, _lock:
            st.markdown('**Requested**')
            st.markdown(f"<h2 style='text-align: left; color: #3c9992;'>{total_inventory_requestedEC11}</h2>", unsafe_allow_html=True)
        with column03_inventory, _lock:
            st.markdown('**Replenishment**')
            st.markdown(f"<h2 style='text-align: left; color: #d0c101;'>{total_replenishmentEC11}</h2>", unsafe_allow_html=True)


        st.markdown('##')
        st.subheader('GBB-CM18')

        total_inventory_balanceCM18 = dfCM18['Quantity'].sum()
        total_inventory_requestedCM18 = dfCM18['Request to draw or add'].sum()
        total_replenishmentCM18 = 0

        column04_inventory, column05_inventory, column06_inventory = st.columns(3)

        with column04_inventory, _lock:
            st.markdown('**Balance**')
            st.markdown(f"<h2 style='text-align: left; color: #703bef;'>{total_inventory_balanceCM18}</h2>",
                        unsafe_allow_html=True)
        with column05_inventory, _lock:
            st.markdown('**Requested**')
            st.markdown(f"<h2 style='text-align: left; color: #3c9992;'>{total_inventory_requestedCM18}</h2>",
                        unsafe_allow_html=True)
        with column06_inventory, _lock:
            st.markdown('**Replenishment**')
            st.markdown(f"<h2 style='text-align: left; color: #d0c101;'>{total_replenishmentCM18}</h2>",
                        unsafe_allow_html=True)

        html_card_subheader_inventoriesEC11 = """
            <div class="card">
              <div class="card-body" style="border-radius: 10px 10px 0px 0px; background:#ff4f00; padding-top: 5px; width: 600px;
               height: 50px;">
                <h3 class="card-title" style="background-color:#ff4f00; color:#eabd1d; font-family:Georgia; text-align: center; padding: 0px 0;">Inventory Movement Morning-EC11</h3>
              </div>
            </div>
            """
        st.markdown('##')
        st.markdown('##')
        st.markdown(html_card_subheader_inventoriesEC11, unsafe_allow_html=True)
        st.markdown('##')

        xinventories_daily = serEC11_daily.index
        yinventories_daily = serEC11_daily.values
        yinventories_mean = serEC11_daily.values.mean()

        figinventories_daily, figinventories_fast = st.columns(2)

        with figinventories_daily, _lock:
            figinventories_daily = go.Figure(data=go.Scatter(x=xinventories_daily, y=yinventories_daily, mode='lines+markers+text', line=dict(color='#13bbaf', width=3),
                                    text=yinventories_daily, textfont=dict(family='sana serif', size=14, color='#c4fff7'), textposition='top center'))
            figinventories_daily.add_hline(y=yinventories_mean, line_dash='dot', line_color='#96ae8d', line_width=2, annotation_text='Average Line',
                                    annotation_position='bottom right', annotation_font_size=18, annotation_font_color='green')
            figinventories_daily.update_xaxes(title_text='Date', tickangle=-45, title_font_color='#74a662', tickmode='linear',
                                       range=[1, 31], showgrid=False, showline=True, linewidth=1, linecolor='#59656d')
            figinventories_daily.update_yaxes(title_text='Number of Inventory', title_font_color='#74a662', tickmode='linear', showgrid=False,
                                       gridwidth=0.1, gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
            figinventories_daily.update_layout(title='Daily Movement', plot_bgcolor='rgba(0, 0, 0, 0)',
                                     # xaxis=dict(showticklabels=True, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
                                     # yaxis=dict(showticklabels=True, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)'))
                                     )
            st.plotly_chart(figinventories_daily, use_container_width=True)

        xinventories_fast = serEC11fast.index
        yinventories_fast = serEC11fast.values

        with figinventories_fast, _lock:
            figinventories_fast = go.Figure(data=[go.Bar(x=yinventories_fast, y=xinventories_fast, text=yinventories_fast,
                                                         orientation='h', textfont=dict(family='sana serif', size=14, color='#c4fff7'),
                                                        textposition='outside', textangle=0)
                                                ])
            figinventories_fast.update_xaxes(title_text="Number of Inventory", tickangle=-45, title_font_color='#087871', showgrid=True,
                                             gridwidth=0.1, gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
            figinventories_fast.update_yaxes(title_text='Description', title_font_color='#087871', showgrid=False, gridwidth=0.1,
                                gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
            figinventories_fast.update_traces(marker_color='#087871', marker_line_color='#087871', marker_line_width=1)
            figinventories_fast.update_layout(title='Fast Moving Inventories', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(figinventories_fast, use_container_width=True)

        html_card_subheader_inventoriesCM18 = """
            <div class="card">
              <div class="card-body" style="border-radius: 10px 10px 0px 0px; background:#ff4f00; padding-top: 5px; width: 600px;
               height: 50px;">
                <h3 class="card-title" style="background-color:#ff4f00; color:#eabd1d; font-family:Georgia; text-align: center; padding: 0px 0;">Inventory Movement Morning-CM18</h3>
              </div>
            </div>
            """
        st.markdown('##')
        st.markdown('##')
        st.markdown(html_card_subheader_inventoriesCM18, unsafe_allow_html=True)
        st.markdown('##')
        st.dataframe(dfCM18)


elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')



hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """
st.markdown(hide_menu_style, unsafe_allow_html=True)
