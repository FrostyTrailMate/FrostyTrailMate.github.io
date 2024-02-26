import { MapContainer, TileLayer, GeoJSON, FeatureGroup} from 'react-leaflet';
import React, { useState, useEffect, useRef,createContext} from 'react';

import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import { EditControl } from 'react-leaflet-draw';
import TrailsYosemite from './geojsons/Trails.json'; // Import GeoJSON data file

import 'react-datepicker/dist/react-datepicker.css';
import './CCStyles/MapCreate.css';
import './CCStyles/Create.css';


export const DrawnItemsContext = createContext([]);

function MapCreate() {

  // Map Constants

  const [basemap, setBasemap] = useState('stamenTerrain');
  const [showTrails, setShowTrails] = useState(true);
  const [drawnItems, setDrawnItems] = useState([]);
  const drawControlRef = useRef(null);

  useEffect(() => {
    if (drawControlRef.current) {
      drawControlRef.current.leafletElement.options.edit.featureGroup.clearLayers();
    }
  }, [showTrails]);

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

  const purpleTrailStyle = {
    color: '#A348B2', // Light purple color
    weight: 1.2, // Adjust the weight of the trail
  };

  const onEachFeature = (feature, layer) => {
    if (feature.properties && feature.properties.popupContent) {
      layer.bindPopup(feature.properties.popupContent);
    }
  };

  const handleDrawCreated = (e) => {
    const layer = e.layer;
    setDrawnItems([...drawnItems, layer]);
  };

  const handleDrawDeleted = () => {
    setDrawnItems([]);
  };

  const handleDrawEdited = (e) => {
    const layers = e.layers;
    const editedItems = layers.getLayers();
    setDrawnItems([...editedItems]);
  };

  return (
    <>
   <DrawnItemsContext.Provider value={[drawnItems, setDrawnItems]}>

    <div className="map-container-c">
      <div className="toggle-container-c">
        <div className="basemap-toggles-c" >
          {Object.keys(basemapUrls).map((key) => (
            <label key={key} className="basemap-toggle-c">
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
        <div className="geojson-toggles-c">
          <label className="geojson-toggle-c">
            <input
              type="checkbox"
              checked={showTrails}
              onChange={handleTrailsToggle}
            />
            <span className="toggle-text-c">Hiking Trails</span>
          </label>
        </div>
      </div>
      <MapContainer
        center={[37.8451, -119.5383]}
        zoom={10}
        className="leaflet-container-c"
      >
        <TileLayer
          url={basemapUrls[basemap]}
          subdomains={['mt0', 'mt1', 'mt2', 'mt3']}
          attribution={basemapAttributions[basemap]}
        />
        {showTrails && (
          <GeoJSON data={TrailsYosemite} style={purpleTrailStyle} onEachFeature={onEachFeature} />
        )}

        <FeatureGroup>
          <EditControl
            position="topright"
            onCreated={handleDrawCreated}
            onEdited={handleDrawEdited}
            onDeleted={handleDrawDeleted}
            draw={{
              rectangle: {
                allowIntersection: false,
                /*shapeOptions: {color: '#426980'},*/
              },
              circle: false,
              circlemarker: false,
              marker: false,
              polyline: false,
              polygon: false,
            }}
            ref={drawControlRef}
          />
        </FeatureGroup>
      </MapContainer>
      <div>
        <ul>
          {drawnItems.map((item, index) => (
            <li key={index}>
              Rectangle {index + 1}: {JSON.stringify(item.getBounds())}
            </li>
          ))}
        </ul>
      </div>
    </div>
    </DrawnItemsContext.Provider>
    </>
  );
}

export const drawnItems = [/* Your drawn items */];

export function getDrawnItemsLength() {
  return drawnItems.length;
}

export default MapCreate;
