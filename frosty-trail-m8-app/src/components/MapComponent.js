import React, { useState } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './CCStyles/MapComponent.css'; // Import external CSS file
import TrailsYosemite from './geojsons/trails.json'; // Import GeoJSON data file
import ElevationPolygons from './geojsons/ElevationPolygons.json'; // Import GeoJSON data file for ElevationPolygons


const MapComponent = () => {
  const [showTrails, setShowTrails] = useState(true);
  const [showElevation, setShowElevation] = useState(true);

  const handleTrailsToggle = () => {
    setShowTrails(!showTrails);
  };

  const handleElevationToggle = () => {
    setShowElevation(!showElevation);
  };

  const purpleTrailStyle = {
    color: '#A348B2', // Light purple color
    weight: 1.2, // Adjust the weight of the trail
  };

  const lightBluePolygonStyle = {
    fillColor: '#add8e6', // Light blue color
    color: '#555', // Grey color for contour lines
    weight: 0.5, // Adjust the weight of the polygon
    fillOpacity: 0.5,
  };

  const onEachFeature = (feature, layer) => {
    if (feature.properties && feature.properties.popupContent) {
      layer.bindPopup(feature.properties.popupContent);
    }
  };

  return (
    <div className="map-container">
      <div className="toggle-container">
        <label className="toggle-label">
          <input
            type="checkbox"
            checked={showTrails}
            onChange={handleTrailsToggle}
          />
          <span className="toggle-text">Hiking Trails</span>
        </label>
        <label className="toggle-label">
          <input
            type="checkbox"
            checked={showElevation}
            onChange={handleElevationToggle}
          />
          <span className="toggle-text">Snow Coverage</span>
        </label>
      </div>
      <MapContainer
        center={[37.8451, -119.5383]}
        zoom={11}
        className="leaflet-container"
      >
        <TileLayer
          url="https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=749cd9dc6622478d9454b931ded7943d"
          subdomains={['mt0', 'mt1', 'mt2', 'mt3']}
          attribution="© Thunderforest by Gravitystorm Limited."
        />

        {showElevation && (
          <GeoJSON data={ElevationPolygons} style={lightBluePolygonStyle} onEachFeature={onEachFeature} />
        )}

        {showTrails && (
          <GeoJSON data={TrailsYosemite} style={purpleTrailStyle} onEachFeature={onEachFeature} />
        )}
      </MapContainer>
    </div>
  );
};

export default MapComponent;





