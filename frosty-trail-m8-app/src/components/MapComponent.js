import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import YosemiteBoundaries from './geojsons/YosemiteBoundaries.json'; // Import GeoJSON data file

const MapComponent = () => {
  const [geojsonData, setGeojsonData] = useState(null);

  useEffect(() => {
    setGeojsonData(YosemiteBoundaries); // Set GeoJSON data when component mounts
  }, []);

  return (
    <div style={{ backgroundColor: '#242424', padding: '60px' }}>
      <MapContainer
        center={[37.8451, -119.5383]}
        zoom={10}
        style={{ height: '690px', width: '85%', margin: '0 auto' }}>

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