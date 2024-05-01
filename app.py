import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
import random
from PIL import Image
from tensorflow.python.keras.callbacks import EarlyStopping
import os
from datetime import datetime

import tensorflow
import tensorflow as tf
kerass = tf.keras
mod = kerass.models

# from keras.models import load_model
# from tensorflow.keras.initializers import Orthogonal

url = 'dff2.csv'
# print(os.getcwd())
# url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTXFKefF7-wy_GWu-tWyI9BFW_HYNB16mGO5yCkQ57I_JraswJO6LHmXEpMjE4myWB_nH2bPP--sQwm/pub?gid=0&single=true&output=csv'
data = pd.read_csv(url)
data['Datetime'] = pd.to_datetime(data['Datetime'], format='%d-%m-%Y %H:%M')

pollutant_parameters = list(data.columns[2:13])
# weather_parameters = list(data.columns[6:10]) + [data.columns[11]]
# print(weather_parameters)

# Define the custom category order
custom_category_order = [
    "Good",
    "Moderate",
    "Unhealthy for Sensitive Groups",
    "Unhealthy",
    "Very Unhealthy",
    "Hazardous"
]



page_names = ['Analytics', 'Prediction']
st.write('<style>div.row-widget.stRadio > div{flex-direction:row;justify-content: center;} </style>', unsafe_allow_html=True)

st.write('<style>div.st-bf{flex-direction:column;} div.st-ag{font-weight:bold;padding-left:2px;padding-right:20px;}</style>', unsafe_allow_html=True)
page = st.sidebar.radio('',page_names)
if page == 'Analytics':
    try:
        st.title('Air Quality Dashboard 2015 - 2020 in 26 Indian Cities')
        with st.sidebar:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(' ')
            with col2:
                st.image("https://cdn1.iconfinder.com/data/icons/air-pollution-21/62/Air-quality-mask-pollution-protection-256.png"
                         , width=100)
            with col3:
                st.write(' ')
            st.header('Filters')


        # Station filter with multiselect
        selected_stations = st.sidebar.multiselect('Select Cities', ['Overall Cities'] + list(data['City'].unique()))

        selected_category = st.sidebar.selectbox('Select Category',
                                                 ['Overall Category'] + list(data['AQI_bucket_calculated'].unique()), index=0)
        start_date = st.sidebar.date_input('Start Date', min(data['Datetime']).date(),
                                           min_value=pd.to_datetime('01-01-2015').date(),
                                           max_value=pd.to_datetime('07-01-2020').date())
        end_date = st.sidebar.date_input('End Date', max(data['Datetime']).date(),
                                         min_value=pd.to_datetime('01-01-2015').date(),
                                         max_value=pd.to_datetime('07-01-2020').date())
        start_hour = st.sidebar.slider('Start Hour', 0, 23, 0)
        end_hour = st.sidebar.slider('End Hour', 0, 23, 23)

        # Filter data based on selected stations
        if 'Overall Cities' in selected_stations:
            selected_stations.remove('Overall Cities')

        start_datetime = pd.to_datetime(start_date).date
        end_datetime = pd.to_datetime(end_date).date
        data['date'] = data['Datetime'].dt.date
        data['Hour'] = data['Datetime'].dt.hour

        # Filter data based on selected stations
        if 'Overall Cities' in selected_stations:
            selected_stations.remove('Overall Cities')

        if selected_category == 'Overall Category' and not selected_stations:
            # If no specific stations are selected, use all stations
            filtered_data = data[(data['date'] >= start_datetime()) & (data['date'] <= end_datetime()) &
                                 (data['Hour'] >= start_hour) & (data['Hour'] <= end_hour)]
        elif not selected_stations:
            filtered_data = data[(data['AQI_bucket_calculated'] == selected_category) &
                                 (data['date'] >= start_datetime()) & (data['date'] <= end_datetime()) &
                                 (data['Hour'] >= start_hour) & (data['Hour'] <= end_hour)]
        elif selected_category == 'Overall Category':
            filtered_data = data[(data['City'].isin(selected_stations)) &
                                 (data['date'] >= start_datetime()) & (data['date'] <= end_datetime()) &
                                 (data['Hour'] >= start_hour) & (data['Hour'] <= end_hour)]
        else:
            filtered_data = data[(data['City'].isin(selected_stations)) & (data['AQI_bucket_calculated'] == selected_category) &
                                 (data['date'] >= start_datetime()) & (data['date'] <= end_datetime()) &
                                 (data['Hour'] >= start_hour) & (data['Hour'] <= end_hour)]


        selected_station_str = ', '.join(selected_stations) if selected_stations else 'All Cities'
        st.write(f"**Key Metrics for {selected_station_str} - {selected_category}**")
        category_counts = filtered_data.groupby('AQI_bucket_calculated')['Datetime'].nunique()
        cols = st.columns(3)
        for index, (category, count) in enumerate(category_counts.items()):
            formatted_count = "{:,}".format(count)  # Format count with commas for thousands
            col = cols[index % 3]  # Cycle through the columns (3 columns)
            col.metric(category, f"{formatted_count} Hours")

        # Calculate counts for each category and set the custom order
        category_counts = data['AQI_bucket_calculated'].value_counts().reset_index()
        category_counts.columns = ['AQI_bucket_calculated', 'Count']
        category_counts['AQI_bucket_calculated'] = pd.Categorical(category_counts['AQI_bucket_calculated'], categories=custom_category_order, ordered=True)
        category_counts = category_counts.sort_values('AQI_bucket_calculated')

        # Create a pie chart
        fig = px.pie(category_counts, values='Count', names='AQI_bucket_calculated', title='Air Quality Categories Percentage')

        # Display the chart in Streamlit
        st.plotly_chart(fig)


        col1, col2 = st.columns(2)
        with col1:
            selected_parameter = st.selectbox('Select Air Pollutant Parameter', pollutant_parameters)
        with col2:
            frequency_options = ['Hourly', 'Daily', 'Weekly', 'Monthly', 'Yearly']
            selected_frequency = st.selectbox('Select Time Frequency', frequency_options)

        # Plot the chart for the selected stations
        filtered_data_resampled = filtered_data.groupby(['City',
                                                         pd.Grouper(key='Datetime',
                                                                    freq=selected_frequency[0])])[selected_parameter].mean().reset_index()
        fig = px.line(filtered_data_resampled, x='Datetime', y=selected_parameter, color='City',
                      title=f'{selected_parameter} {selected_frequency} Levels by City Over Time')
        st.plotly_chart(fig)


        # Display Scatter Plot
        col1, col2 = st.columns(2)
        with col1:
            selected_parameter1 = st.selectbox('Select Parameter 1', pollutant_parameters)
        with col2:
            selected_parameter2 = st.selectbox('Select Parameter 2', pollutant_parameters)

        fig_scatter = px.scatter(filtered_data, x=selected_parameter1, y=selected_parameter2,
                                 color='City', title=f'{selected_parameter1} vs. {selected_parameter2} Correlation')
        st.plotly_chart(fig_scatter)


        # Group and pivot the data to get the counts for each category and station
        pivot_data = filtered_data.pivot_table(index='City', columns='AQI_bucket_calculated', values='AQI_calculated', aggfunc='count', fill_value=0)

        # Create a stacked bar chart
        fig = px.bar(pivot_data, x=pivot_data.index, y=custom_category_order, title='Air Quality by City',
                     labels={'City': 'City', 'value': 'Count', 'variable': 'AQI_bucket_calculated'},
                     color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_layout(barmode='stack')

        # Display the chart in Streamlit
        st.plotly_chart(fig)


        # Map categories to a numerical order based on the custom order
        category_order_mapping = {category: i for i, category in enumerate(custom_category_order)}

        # Assign a numerical order to each row in the dataset
        data['Category_Order'] = filtered_data['AQI_bucket_calculated'].map(category_order_mapping)

        # # Group and aggregate data
        grouped_data = data.groupby(['AQI_bucket_calculated']).size().reset_index(name='count')

        # Sort the data based on the custom category order and category order mapping
        grouped_data['Category_Order'] = grouped_data['AQI_bucket_calculated'].map(category_order_mapping)
        grouped_data = grouped_data.sort_values(by=['Category_Order'])

        # Create a colormap with varying shades of a single color (e.g., blue)
        color_scale = pc.sequential.Blues

        # Create polar bar chart
        fig = go.Figure()

        categories = custom_category_order
    except Exception as e:
        warning = '<p style="color:Red; font-size: 30px; font-weight: bold;">Enter Details First!!</p>'
        st.markdown(warning, unsafe_allow_html=True)
else:
    try:
        st.title('Prediction based on data from 2023-Present')
        with st.sidebar:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(' ')
            with col2:
                st.image("https://cdn1.iconfinder.com/data/icons/air-pollution-21/62/Air-quality-mask-pollution-protection-256.png"
                         , width=100)
            with col3:
                st.write(' ')
            st.header('Filters')
            state_ticker = st.sidebar.selectbox('Select State:', options=['Uttar Pradesh','Orissa','Madhya Pradesh', 'Rajasthan', 'Gujarat', 'Himachal Pradesh', 'Chhattisgarh', 'Jammu and Kashmir', 'Daman and Diu', 'Andhra Pradesh', 'Jharkhand', 'Bihar', 'West Bengal', 'Maharashtra', 'Haryana', 'Chandigarh', 'Goa', 'Andaman and Nicobar Islands', 'Arunachal Pradesh', 'Assam','Kerala', 'Mizoram', 'Manipur', 'Nagaland', 'Tripura', 'Karnataka', 'Uttarakhand','Punjab', 'TamilNadu','Delhi'])

            # st.title("Date and Hour Input Example")
            selected_date = st.date_input("Select a date")

        # Hour input (with one-hour intervals)
            selected_hour = st.slider("Select an hour", 0, 23, step=1)

        # Create a datetime object
            selected_datetime = datetime(
            selected_date.year,
            selected_date.month,
            selected_date.day,
            selected_hour,
            0,  # Set minutes to 0
            0   # Set seconds to 0
            )



        

        model = mod.load_model('aqi_lstm_model_%s.h5'% (state_ticker))
        temp = list(selected_date.year, selected_date.month, selected_date.day, selected_hour)
        inpu = pd.DataFrame(temp)
        aqi = model.predict(inpu)
        aqi = int(aqi)
        final_result = "The Predicted US-EPA index is "+ str(custom_category_order[aqi-1])
        
        if aqi >= 5:
            st.write(f"<p style='font-size: 30px; color: red;'>Predicted US-EPA index: {custom_category_order[aqi-1]}</p>",
                     unsafe_allow_html=True)

        elif aqi >= 3:
            st.write(f"<p style='font-size: 30px; color: orange;'>Predicted US-EPA index: {custom_category_order[aqi-1]}</p>",
                     unsafe_allow_html=True)
        
        else:
            st.write(f"<p style='font-size: 30px; color: green;'>Predicted US-EPA index: {custom_category_order[aqi-1]}</p>",
                     unsafe_allow_html=True)
           
    except Exception as e:
        warning = '<p style="color:Red; font-size: 30px; font-weight: bold;">Enter Details First!!</p>'
        st.markdown(warning, unsafe_allow_html=True)

    




