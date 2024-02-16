import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './CCStyles/MapComponent.css'; // Import external CSS file
import YosemiteBoundaries from './geojsons/YosemiteBoundaries.json'; // Import GeoJSON data file

const MapComponent = () => {
  const [geojsonData, setGeojsonData] = useState(null);

  useEffect(() => {
    setGeojsonData(YosemiteBoundaries); // Set GeoJSON data when component mounts
  }, []);

  return (
    <div className="map-container">
      <MapContainer
        center={[37.8451, -119.5383]}
        zoom={10}
        className="leaflet-container">

        <TileLayer
          url="https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=749cd9dc6622478d9454b931ded7943d"
          subdomains={['mt0', 'mt1', 'mt2', 'mt3']}
          attribution='© Thunderforest by Gravitystorm Limited.'/>

        {geojsonData && (
          <GeoJSON data={geojsonData} />
        )}
      </MapContainer>
    </div>
  );
};

export default MapComponent;
