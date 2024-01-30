// MyMapComponent.js

import React from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const MapComponent = () => {
  return (
    <MapContainer
      center={[37.7749, -122.4194]} // Set the initial center (latitude, longitude)
      zoom={13} // Set the initial zoom level
      style={{ height: '400px', width: '100%' }} // Set the map container size
    >
      <TileLayer
        url="https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"
        subdomains={['mt0', 'mt1', 'mt2', 'mt3']}
        attribution='&copy; Google'
      />
    </MapContainer>
  );
};

export default MapComponent;
