import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import './CSStyles/MapComponent.css'; // Import external CSS file

const MapComponent = ({ selectedArea }) => {
  const [basemap, setBasemap] = useState('stamenTerrain');
  const [showElevation, setShowElevation] = useState(true);
  const [geojsonData, setGeojsonData] = useState(null);
  const [refreshMap, setRefreshMap] = useState(false); // State to trigger map refresh
  const [mapCenter, setMapCenter] = useState([37.8451, -119.5383]); // Default center
  const [selectedFeatures, setSelectedFeatures] = useState([]); // State to keep track of selected features

  const basemapUrls = {
    stamenTerrain: 'https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png',
    esriWorldTopoMap: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
    esriWorldImagery: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
  };

  const basemapAttributions = {
    stamenTerrain: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC BY SA</a>.',
    esriWorldTopoMap: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community',
    esriWorldImagery: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
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
  const isSelected = selectedFeatures.includes(feature);
  const coveragePercentage = feature.properties.coverage_percentage;
  const opacity = coveragePercentage ? coveragePercentage / 100 : 1; // Assuming coverage_percentage is a percentage value
  
  return {
    color: '#000000',
    weight: 0.4,
    fill: true,
    fillColor: isSelected ? 'rgb(255, 126, 241)' : '#ffffff', // Highlight if selected
    fillOpacity: opacity,
    dashArray: '4', // Example: a dash pattern with 5px dashes followed by 5px gaps

    smoothFactor: 1, // Example: no smoothing
    className: 'custom-polygon-class' // Example: add a custom class for additional styling
  };
};


  const selectFeaturesWithSameElevation = (feature) => {
    const elevation = feature.properties.elevation;
    const featuresWithSameElevation = geojsonData.features.filter(f => f.properties.elevation === elevation);
    setSelectedFeatures(featuresWithSameElevation);
  };

  return (
    
    <div className="map-container">
      <div className="toggle-container">
        <div className="basemap-toggles" >
        <strong >Select your Basemap: </strong>
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
              {key === 'esriWorldTopoMap' && ' Topographic Map  '}
              {key === 'esriWorldImagery' && ' World Imagery  '}
            </label>
          ))}
        </div>
        <div className="geojson-toggles">
          <label className="geojson-toggle">
            <input type="checkbox" checked={showElevation} onChange={handleElevationToggle}/>
            <span className="toggle-text">Snow Coverage Layer: {selectedArea}</span>
          </label>
              <button className='ButtonRefreshMap'
                onClick={handleRefreshMap}>
                Center Map to Layer
              </button>
        </div>
      </div>
      <MapContainer style={{zIndex:'10'}}
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
              layer.on({
                click: () => selectFeaturesWithSameElevation(feature) // Select features with same elevation on click
              });
              layer.bindPopup(`<strong>Elevation:</strong> ${feature.properties.elevation}<br><strong>Coverage Percentage:</strong> ${feature.properties.coverage_percentage}%`);

            }}
          />
        )}
      </MapContainer>
    </div>
  );
};

export default MapComponent;
