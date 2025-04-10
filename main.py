import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import base64

# Function to get Strava token from URL parameters (OAuth)
def get_token_from_url():
    # Check if the OAuth authorization code exists in the URL
    if 'code' in st.experimental_get_query_params():
        authorization_code = st.experimental_get_query_params()['code'][0]
        client_id = 'your_client_id_here'  # Replace with your Strava app client ID
        client_secret = 'your_client_secret_here'  # Replace with your Strava app client secret
        redirect_uri = 'your_redirect_uri_here'  # Replace with the redirect URI you set in Strava
        
        # Prepare the payload for token exchange
        token_url = 'https://www.strava.com/api/v3/oauth/token'
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': authorization_code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }

        # Make a POST request to exchange the authorization code for an access token
        response = requests.post(token_url, data=payload)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            refresh_token = token_data.get('refresh_token')
            expires_at = token_data.get('expires_at')
            return access_token, refresh_token, expires_at
        else:
            st.error('Failed to exchange code for token')
            return None, None, None
    return None, None, None

# Function to get Strava data
def get_strava_data(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://www.strava.com/api/v3/athlete', headers=headers)
    
    if response.status_code == 200:
        return response.json()  # Returns the JSON data from the API
    else:
        st.error('Failed to fetch data from Strava')
        return None

# Function to get activity data
def get_strava_activities(access_token):
    activities_url = 'https://www.strava.com/api/v3/athlete/activities'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'per_page': 10}  # Get the most recent 10 activities
    response = requests.get(activities_url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()  # Returns activity data as a list of dictionaries
    else:
        st.error('Failed to fetch activities')
        return None

# Streamlit interface for the app
st.title('Strava Data Dashboard')

# Step 1: Check if the token is available
access_token = st.session_state.get('access_token')
if access_token is None:
    st.write("You need to authenticate first.")
    # Step 2: Show the authorization URL for OAuth
    client_id = 'your_client_id_here'  # Replace with your Strava app client ID
    redirect_uri = 'your_redirect_uri_here'  # Replace with the redirect URI
    auth_url = f"https://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope=read&state=your_state_here"
    st.markdown(f"Click [here to authenticate]( {auth_url} ).")
else:
    # Step 3: If access_token exists, allow user to fetch data
    st.write("You are authenticated!")

    # Button to fetch Strava data
    if st.button('Load Athlete Data'):
        athlete_data = get_strava_data(access_token)
        
        if athlete_data:
            st.subheader('Athlete Information')
            st.write(athlete_data)

    # Display recent activities
    st.subheader('Recent Activities')
    activities = get_strava_activities(access_token)

    if activities:
        # Convert the activities data into a Pandas DataFrame for better visualization
        activities_df = pd.DataFrame(activities)
        st.write(activities_df[['name', 'distance', 'moving_time', 'type', 'start_date']])

        # Plotting activity types
        activity_types = activities_df['type'].value_counts()
        st.bar_chart(activity_types)

        # Plotting distance of activities
        plt.figure(figsize=(8, 4))
        plt.bar(activities_df['name'], activities_df['distance'] / 1000)  # Convert distance to km
        plt.title('Distance of Recent Activities (in km)')
        plt.xlabel('Activity')
        plt.ylabel('Distance (km)')
        plt.xticks(rotation=45)
        st.pyplot(plt)

    # Save the access_token for future sessions (to avoid re-authentication)
    st.session_state['access_token'] = access_token

# Footer
st.markdown('Made with ❤️ using Streamlit')
