// MapWithDrawing.js

import React, { useEffect } from 'react';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import L from 'leaflet';
import 'leaflet-draw';

const MapWithDrawing = () => {
  useEffect(() => {
    // Initialize Leaflet Map
    const map = L.map('map').setView([37.8651, -119.5383], 10);

    // Add OpenStreetMap Tile Layer WILL EXPIRE IN THE 29TH
    L.tileLayer('https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=749cd9dc6622478d9454b931ded7943d', {
      attribution: '© Thunderforest is a project by Gravitystorm Limited.'
    }).addTo(map);

    // Initialize Leaflet.draw
    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    const drawControl = new L.Control.Draw({
      edit: {
        featureGroup: drawnItems
      }
    });
    map.addControl(drawControl);

    // Capture Coordinates on Draw or Edit
    map.on('draw:created', (e) => {
      const type = e.layerType;
      const layer = e.layer;

      if (type === 'polygon') {
        // Access polygon coordinates
        const coordinates = layer.getLatLngs();
        console.log(coordinates);
      }

      drawnItems.addLayer(layer);
    });

    map.on('draw:edited', (e) => {
      const layers = e.layers;
      layers.eachLayer((layer) => {
        if (layer instanceof L.Polygon) {
          // Access edited polygon coordinates
          const coordinates = layer.getLatLngs();
          console.log(coordinates);
        }
      });
    });
  }, []); // Run useEffect only once on component mount

  return <div id="map" style={{ height: '600px' }}></div>;
};

export default MapWithDrawing;
