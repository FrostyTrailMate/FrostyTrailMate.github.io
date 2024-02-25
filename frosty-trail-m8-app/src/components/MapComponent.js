import React, { useState } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './CCStyles/MapComponent.css'; // Import external CSS file
import TrailsYosemite from './geojsons/Trails.json'; // Import GeoJSON data file
import BoundaryPolygon from './geojsons/YosemiteBoundary.json'; // Import GeoJSON data file

const MapComponent = () => {
  const [basemap, setBasemap] = useState('thunderforest');
  const [showTrails, setShowTrails] = useState(true);
  const [showElevation, setShowElevation] = useState(true);

  const basemapUrls = {
    thunderforest: 'https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=749cd9dc6622478d9454b931ded7943d',
    openStreetMap: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    stamenTerrain: 'https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png',
  };

  const basemapAttributions = {
    thunderforest: '© Thunderforest by Gravitystorm Limited.',
    openStreetMap: '© OpenStreetMap contributors',
    stamenTerrain: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC BY SA</a>.',
  };

  const handleBasemapChange = (newBasemap) => {
    setBasemap(newBasemap);
  };

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
    color: '#555', // Grey color for contour lines
    weight: 2, // Adjust the weight of the polygon
    fill: false, // Fill the polygon with color
  };

  const onEachFeature = (feature, layer) => {
    if (feature.properties && feature.properties.popupContent) {
      layer.bindPopup(feature.properties.popupContent);
    }
  };

  return (
    <div className="map-container">
      <div className="toggle-container">
        <div className="basemap-toggles">
          {Object.keys(basemapUrls).map((key) => (
            <label key={key} className="basemap-toggle">
              <input
                type="radio"
                name="basemap"
                value={key}
                checked={basemap === key}
                onChange={() => handleBasemapChange(key)}
              />
              {key === 'thunderforest' && 'Thunderforest'}
              {key === 'openStreetMap' && 'OpenStreetMap'}
              {key === 'stamenTerrain' && 'Stamen Terrain'}
            </label>
          ))}
        </div>
        <div className="geojson-toggles">
          <label className="geojson-toggle">
            <input
              type="checkbox"
              checked={showTrails}
              onChange={handleTrailsToggle}
            />
            <span className="toggle-text">Hiking Trails</span>
          </label>
          <label className="geojson-toggle">
            <input
              type="checkbox"
              checked={showElevation}
              onChange={handleElevationToggle}
            />
            <span className="toggle-text">Boundary</span>
          </label>
        </div>
      </div>
      <MapContainer
        center={[37.8451, -119.5383]}
        zoom={10}
        className="leaflet-container"
      >
        <TileLayer
          url={basemapUrls[basemap]}
          subdomains={['mt0', 'mt1', 'mt2', 'mt3']}
          attribution={basemapAttributions[basemap]}
        />

        {showElevation && (
          <GeoJSON data={BoundaryPolygon} style={lightBluePolygonStyle} onEachFeature={onEachFeature} />
        )}

        {showTrails && (
          <GeoJSON data={TrailsYosemite} style={purpleTrailStyle} onEachFeature={onEachFeature} />
        )}
      </MapContainer>
    </div>
  );
};

export default MapComponent;


