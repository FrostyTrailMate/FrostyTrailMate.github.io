import React, { useState } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './CCStyles/MapComponent.css'; // Import external CSS file
import TrailsYosemite from './geojsons/Trails.json'; // Import GeoJSON data file
import SnowCoverage from './geojsons/ElevationPolygons.json'; // Import GeoJSON data file

const MapComponent = () => {
  const [basemap, setBasemap] = useState('stamenTerrain');
  const [showTrails, setShowTrails] = useState(true);
  const [showElevation, setShowElevation] = useState(true);

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
    weight: 0.3, // Adjust the weight of the polygon
    fill: true, // Fill the polygon with color
    fillColor: '#A6CEE3', // Light blue color
    fillOpacity: 0.3, // Adjust the opacity of the fill
  };

  const onEachFeature = (feature, layer) => {
    if (feature.properties && feature.properties.popupContent) {
      layer.bindPopup(feature.properties.popupContent);
    }
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
            <span className="toggle-text">Snow Coverage</span>
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
          <GeoJSON data={SnowCoverage} style={lightBluePolygonStyle} onEachFeature={onEachFeature} />
        )}

        {showTrails && (
          <GeoJSON data={TrailsYosemite} style={purpleTrailStyle} onEachFeature={onEachFeature} />
        )}
      </MapContainer>
    </div>
  );
};

export default MapComponent;


