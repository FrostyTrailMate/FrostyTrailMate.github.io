import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import './CCStyles/MapComponent.css'; // Import external CSS file

const MapComponent = ({ selectedArea }) => {
  const [basemap, setBasemap] = useState('stamenTerrain');
  const [showElevation, setShowElevation] = useState(true);
  const [geojsonData, setGeojsonData] = useState(null);
  const [refreshMap, setRefreshMap] = useState(false); // State to trigger map refresh
  const [mapCenter, setMapCenter] = useState([37.8451, -119.5383]); // Default center

  const basemapUrls = {
    stamenTerrain: 'https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png',
    thunderforest: 'https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=749cd9dc6622478d9454b931ded7943d',
    openStreetMap: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
  };

  const basemapAttributions = {
    stamenTerrain: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC BY SA</a>.',
    thunderforest: '© Thunderforest by Gravitystorm Limited.',
    openStreetMap: '© OpenStreetMap contributors',
  };

  useEffect(() => {
    if (selectedArea) {
      // Load GeoJSON data for the selected area from Flask server
      axios.get(`http://127.0.0.1:5000/api/geojson/${selectedArea}`)
        .then(response => {
          const data = response.data;
          setGeojsonData(data);
  
          // Set map center when geojsonData is updated
          if (data && data.features.length > 0) {
            const coordinates = data.features[0].geometry.coordinates[0][0];
            setMapCenter([coordinates[1], coordinates[0]]);
          }
        })
        .catch(error => {
          console.error('Error fetching GeoJSON data:', error);
        });
    }
  }, [selectedArea]);

  const handleBasemapChange = (newBasemap) => {
    setBasemap(newBasemap);
  };

  const handleElevationToggle = () => {
    setShowElevation(!showElevation);
  };

  const handleRefreshMap = () => {
    setRefreshMap(prev => !prev); // Toggle refreshMap state to trigger map refresh
  };

  const polygonStyle = (feature) => {
    const coveragePercentage = feature.properties.coverage_percentage;
    const opacity = coveragePercentage ? coveragePercentage / 100 : 1; // Assuming coverage_percentage is a percentage value
    
    return {
      color: '#555',
      weight: 1.5,
      fill: true,
      fillColor: '#006688',
      fillOpacity: opacity,
    };
  };

  return (
    <div className="map-container">
      <div className="toggle-container">
        <div className="basemap-toggles" >
          {Object.keys(basemapUrls).map((key) => (
            <label key={key} className="basemap-toggle">
              <input
                type="radio"
                name="basemap"
                value={key}
                checked={basemap === key}
                onChange={() => handleBasemapChange(key)}
              />
              {key === 'stamenTerrain' && '  Stamen Terrain  '}
              {key === 'thunderforest' && '  Thunderforest  '}
              {key === 'openStreetMap' && '  OpenStreetMap  '}
            </label>
          ))}
        </div>
        <div className="geojson-toggles">
          <label className="geojson-toggle">
            <input
              type="checkbox"
              checked={showElevation}
              onChange={handleElevationToggle}
            />
            <span className="toggle-text">Snow Coverage</span>
          </label>
        </div>
        <button className="refresh-button" onClick={handleRefreshMap}>
          Center Map
        </button>
      </div>
      <MapContainer
        center={mapCenter}
        zoom={10}
        className="leaflet-container"
        key={refreshMap} // Key attribute forces re-render when refreshMap changes
      >
        <TileLayer
          url={basemapUrls[basemap]}
          subdomains={['mt0', 'mt1', 'mt2', 'mt3']}
          attribution={basemapAttributions[basemap]}
        />
        {showElevation && geojsonData && (
          <GeoJSON
            key={JSON.stringify(geojsonData)} // Add key attribute here
            data={geojsonData}
            style={polygonStyle}
            onEachFeature={(feature, layer) => {
              layer.bindPopup(`Elevation: ${feature.properties.elevation}<br>Coverage Percentage: ${feature.properties.coverage_percentage}%`);
            }}
          />
        )}
      </MapContainer>
    </div>
  );
};

export default MapComponent;
