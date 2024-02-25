import React, { useState } from 'react';
import { MapContainer, TileLayer, Rectangle } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import 'leaflet-draw/dist/leaflet.draw.css';
import './CCStyles/MapComponent.css'; // Import external CSS file


const MapComponent = () => {
  const [basemap, setBasemap] = useState('stamenTerrain');
  const [rectangleBounds, setRectangleBounds] = useState(null);

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

  const onRectangleDraw = (e) => {
    const layer = e.layer;
    setRectangleBounds(layer.getBounds());
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
      </div>
      <MapContainer
        center={[0, 0]}
        zoom={2}
        className="leaflet-container"
      >
        <TileLayer
          url={basemapUrls[basemap]}
          subdomains={['mt0', 'mt1', 'mt2', 'mt3']}
          attribution={basemapAttributions[basemap]}
        />
        <EditControl
          position="topright"
          draw={{
            rectangle: true,
            circle: false,
            marker: false,
            polyline: false,
            polygon: false,
            circlemarker: false
          }}
          onCreated={onRectangleDraw}
        />
        {rectangleBounds && (
          <Rectangle bounds={rectangleBounds} />
        )}
      </MapContainer>
    </div>
  );
};

export default MapComponent;
