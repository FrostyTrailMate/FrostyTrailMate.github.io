import React, { useState } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './CCStyles/MapComponent.css'; // Import external CSS file
import YosemiteBoundary from './geojsons/YosemiteBoundary.json'; // Import GeoJSON data file
import ElevationPolygons from './geojsons/ElevationPolygons.json'; // Import GeoJSON data file for ElevationPolygons

const MapComponent = () => {
  const [showBoundary, setShowBoundary] = useState(true);
  const [showElevation, setShowElevation] = useState(true);

  const handleBoundaryToggle = () => {
    setShowBoundary(!showBoundary);
  };

  const handleElevationToggle = () => {
    setShowElevation(!showElevation);
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
            checked={showBoundary}
            onChange={handleBoundaryToggle}
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
        zoom={10}
        className="leaflet-container"
      >
        <TileLayer
          url="https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=749cd9dc6622478d9454b931ded7943d"
          subdomains={['mt0', 'mt1', 'mt2', 'mt3']}
          attribution="© Thunderforest by Gravitystorm Limited."
        />

        {showBoundary && (
          <GeoJSON data={YosemiteBoundary} onEachFeature={onEachFeature} />
        )}

        {showElevation && (
          <GeoJSON data={ElevationPolygons} onEachFeature={onEachFeature} />
        )}
      </MapContainer>
    </div>
  );
};

export default MapComponent;
