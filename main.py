import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import altair as alt

# --- PAGE CONFIG ---
st.set_page_config(page_title="Strava Health Dashboard 🚴‍♂️", layout="wide")

# --- STRAVA ACCESS TOKEN ---
ACCESS_TOKEN = "6f02320cca30a0c03302a35ab2fdd989c27c5471"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

# --- FETCH PROFILE ---
def fetch_profile():
    response = requests.get("https://www.strava.com/api/v3/athlete", headers=HEADERS)
    response.raise_for_status()
    return response.json()

# --- FETCH ACTIVITIES ---
def fetch_activities(per_page=50, pages=2):
    all_activities = []
    for page in range(1, pages + 1):
        response = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers=HEADERS,
            params={"per_page": per_page, "page": page}
        )
        response.raise_for_status()
        activities = response.json()
        if not activities:
            break
        all_activities.extend(activities)
    return all_activities

# --- GET ATHLETE ZONES ---
def fetch_zones():
    response = requests.get("https://www.strava.com/api/v3/athlete/zones", headers=HEADERS)
    response.raise_for_status()
    return response.json()

# --- TITLE ---
st.title("🚴‍♂️ Strava Health Dashboard")

# --- FETCH DATA ---
try:
    with st.spinner("📡 Fetching profile..."):
        profile = fetch_profile()

    with st.spinner("📈 Fetching activities..."):
        activities = fetch_activities()

    with st.spinner("⚙️ Fetching zone data..."):
        zones_data = fetch_zones()

except Exception as e:
    st.error(f"❌ Failed to fetch data: {e}")
    st.stop()

# --- DISPLAY PROFILE INFO ---
st.subheader("🏅 Athlete Profile")

cols = st.columns(3)
cols[0].metric("Name", profile.get('firstname', '') + " " + profile.get('lastname', ''))
cols[1].metric("City", profile.get('city', 'Unknown'))
cols[2].metric("Followers", profile.get('follower_count', 0))

# Handle profile image safely
profile_url = profile.get('profile', '')
if profile_url and profile_url.startswith("http"):
    st.image(profile_url, width=100)
else:
    st.info("No profile image available.")

st.markdown(f"**Account Created:** {profile.get('created_at', 'N/A')}")
st.markdown(f"**Country:** {profile.get('country', 'Unknown')}")
st.markdown(f"**Measurement Preference:** {profile.get('measurement_preference', 'N/A')}")

st.markdown("---")

# --- ACTIVITY COUNT ---
st.subheader("📊 Activity Summary")
total_activities = len(activities)
st.metric("Total Activities Fetched", total_activities)

if not activities:
    st.warning("No activities found.")
    st.stop()

# --- LATEST ACTIVITY ---
latest = activities[0]
st.subheader("🚴 Latest Activity")
st.markdown(f"**{latest.get('name', 'No name')}** on {latest.get('start_date_local', '')}")

cols = st.columns(4)
cols[0].metric("Distance (km)", round(latest.get('distance', 0) / 1000, 2))
cols[1].metric("Time (min)", round(latest.get('moving_time', 0) / 60, 2))
cols[2].metric("Speed (km/h)", round(latest.get('average_speed', 0) * 3.6, 2))
cols[3].metric("Elevation (m)", latest.get('total_elevation_gain', 0))

# --- WEEKLY GOAL ---
st.markdown("### 🎯 Weekly Goal Progress")

week_ago = datetime.now() - timedelta(days=7)
weekly_activities = []
for act in activities:
    try:
        start_date = datetime.strptime(act['start_date_local'], "%Y-%m-%dT%H:%M:%S%z")
        if start_date > week_ago:
            weekly_activities.append(act)
    except:
        continue

total_distance = sum(act.get('distance', 0) for act in weekly_activities) / 1000
goal = 100
progress = min(total_distance / goal, 1.0)

st.progress(progress)
st.markdown(f"**{total_distance:.2f} km** out of **{goal} km** this week")

# --- RECENT ACTIVITIES TABLE ---
st.markdown("### 📋 Recent Activities")

activity_data = [{
    "Name": act.get('name'),
    "Distance (km)": round(act.get('distance', 0) / 1000, 2),
    "Time (min)": round(act.get('moving_time', 0) / 60, 2),
    "Speed (km/h)": round(act.get('average_speed', 0) * 3.6, 2),
    "Date": act.get('start_date_local', '')
} for act in activities[:10]]

st.dataframe(activity_data)

# --- POWER ZONE DISTRIBUTION ---
st.markdown("---")
st.subheader("⚡ Power Zone Distribution")

power_zone = None
if isinstance(zones_data, list):
    for z in zones_data:
        if isinstance(z, dict) and z.get("type") == "power":
            power_zone = z
            break

if power_zone:
    buckets = power_zone.get("distribution_buckets", [])

    df_power = pd.DataFrame([
        {
            "Zone": f"{b['min']}-{b['max'] if b['max'] != -1 else '+'}",
            "Time (sec)": b['time']
        }
        for b in buckets if b['time'] > 0
    ])

    chart = alt.Chart(df_power).mark_bar().encode(
        x=alt.X("Zone:N", sort=None, title="Power Zone (Watts)"),
        y=alt.Y("Time (sec):Q", title="Time Spent (sec)"),
        tooltip=["Zone", "Time (sec)"]
    ).properties(
        width=700,
        height=400,
        title="Time Spent in Each Power Zone"
    )

    st.altair_chart(chart)
else:
    st.warning("No power zone data available.")

# --- HEART RATE ZONES ---
st.markdown("### ❤️ Heart Rate Zones")

try:
    if isinstance(zones_data, dict) and "heart_rate" in zones_data:
        hr_zones = zones_data["heart_rate"]["zones"]

        df_hr = pd.DataFrame([
            {
                "Zone": f"Z{i+1}",
                "Min HR": z["min"],
                "Max HR": z["max"] if z["max"] != -1 else None
            }
            for i, z in enumerate(hr_zones)
        ])

        chart_hr = alt.Chart(df_hr).mark_bar().encode(
            x="Min HR:Q",
            x2="Max HR:Q",
            y=alt.Y("Zone:N", sort=None),
            tooltip=["Zone", "Min HR", "Max HR"]
        ).properties(
            width=700,
            height=300,
            title="Heart Rate Zone Ranges"
        )

        st.altair_chart(chart_hr)
    else:
        st.warning("No heart rate zone data available.")

except Exception as e:
    st.error(f"Failed to process heart rate zones: {e}")

# --- FOOTER ---
st.markdown("---")
st.caption("Built with ❤️ for Strava athletes.")
