// MyMapComponent.js

import React from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const MapComponent = () => {
  return (
    <div style={{ backgroundColor: '#242424', padding: '60px' }}> {/* Set the background color to black */}
      <MapContainer
        center={([37.8651, -119.5383])} // Set the initial center (latitude, longitude) (Lisbon)
        zoom={10} // Set the initial zoom level
        style={{ height: '550px', width: '85%', margin: '0 auto' }} // Set the map container size and center it
      >
        <TileLayer
          url="https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=749cd9dc6622478d9454b931ded7943d"
          subdomains={['mt0', 'mt1', 'mt2', 'mt3']}
          attribution='© Thunderforest by Gravitystorm Limited.'
        />
      </MapContainer>
    </div>
  );
};

export default MapComponent;