import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from scipy.fft import fft
import matplotlib.pyplot as plt
from geopy.distance import geodesic

# Lataa tietojoukot
accel_url = "Accelerometer.csv"  
gps_url = "Location.csv"          
accel_df = pd.read_csv(accel_url)
gps_df = pd.read_csv(gps_url)

# Poista mahdolliset ylimääräiset välilyönnit sarakkeiden nimistä
gps_df.columns = gps_df.columns.str.strip()
accel_df.columns = accel_df.columns.str.strip()

# Laske kiihtyvyyden magnitudi
accel_df['Magnitude'] = np.sqrt(accel_df['X (m/s^2)']**2 + accel_df['Y (m/s^2)']**2 + accel_df['Z (m/s^2)']**2)

# Askelten havaitseminen kiihtyvyyden kynnysarvon perusteella
step_threshold = 1.5  # Säädä kynnysarvoa datan perusteella
accel_df['Step'] = accel_df['Magnitude'] > step_threshold
step_count = accel_df['Step'].sum()

# Laske kokonaismatka GPS-tiedoista
distances = []
for i in range(1, len(gps_df)):
    coord1 = (gps_df.loc[i-1, 'Latitude (°)'], gps_df.loc[i-1, 'Longitude (°)'])
    coord2 = (gps_df.loc[i, 'Latitude (°)'], gps_df.loc[i, 'Longitude (°)'])
    distance_km = geodesic(coord1, coord2).kilometers
    distances.append(distance_km)
gps_df['Distance (km)'] = [0] + distances  # Ensimmäinen arvo on 0
total_distance = gps_df['Distance (km)'].sum()  # Kumulatiivinen etäisyys km

# Keskinopeuden laskenta
average_speed = gps_df['Velocity (m/s)'].mean()
step_length = total_distance * 1000 / step_count if step_count > 0 else 0  # metreinä

# Fourier-muunnos Z-akselille
fs = 50  # Näytteenottotaajuus Hz:ssä (muuta tarvittaessa)
N = len(accel_df['Z (m/s^2)'])
yf = fft(accel_df['Z (m/s^2)'])
xf = np.fft.fftfreq(N, 1/fs)

# Luo sovelluksen otsikko
st.title('Päivän Liikunta')

# Näytä tärkeät tilastot
st.write(f"Yhteensä askelia: {step_count}")
st.write(f"Keskinopeus: {average_speed:.2f} m/s")
st.write(f"Kokonaismatka: {total_distance:.2f} km")
st.write(f"Askelpituus: {step_length:.2f} m")

# Kiihtyvyyden viivakaavio
st.line_chart(accel_df[['Time (s)', 'Z (m/s^2)']].set_index('Time (s)'))

st.title('Suodaten kiihtyvyysdatan y-komponentti')

# Tehospektritiheyden kaavio
plt.figure(figsize=(10, 5))
plt.plot(xf, np.abs(yf), label='Tehospektritiheys')
plt.title('Z-Akselin Kiihtyvyyden Tehospektritiheys')
plt.xlabel('Taajuus (Hz)')
plt.ylabel('Magnitudi')
plt.xlim(0, fs/2)  # Näytä vain positiiviset taajuudet
plt.grid()
st.pyplot(plt)
plt.close()

# Luo kartta reitistä
start_lat = gps_df['Latitude (°)'].mean()
start_long = gps_df['Longitude (°)'].mean()
map = folium.Map(location=[start_lat, start_long], zoom_start=14)
folium.PolyLine(gps_df[['Latitude (°)', 'Longitude (°)']], color='blue', weight=3.5, opacity=1).add_to(map)

# Näytä kartta
st_map = st_folium(map, width=900, height=650)
