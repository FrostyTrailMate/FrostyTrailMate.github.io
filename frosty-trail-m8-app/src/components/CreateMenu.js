import { MapContainer, TileLayer, FeatureGroup} from 'react-leaflet';
import React, { useState, useEffect, useRef } from 'react';
import DatePicker from 'react-datepicker';
import { format } from 'date-fns';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import { EditControl } from 'react-leaflet-draw';

import 'react-datepicker/dist/react-datepicker.css';
import './CCStyles/Create.css';
import './CCStyles/CreateMenu.css';

function CreateMenu() {

  const [basemap, setBasemap] = useState('stamenTerrain');
  const [showTrails, setShowTrails] = useState(true);
  const [drawnItems, setDrawnItems] = useState([]);
  const drawControlRef = useRef(null);

  const updateCoordinates = (key, value) => {
    setCoordinates(prevCoordinates => ({
      ...prevCoordinates,
      [key]: value
    }));
  };

  useEffect(() => {
    if (drawnItems.length > 0) {
      const bounds = drawnItems[0].getBounds();
      updateCoordinates('ymax', bounds._northEast.lat);
      updateCoordinates('xmin', bounds._southWest.lng);
      updateCoordinates('ymin', bounds._southWest.lat);
      updateCoordinates('xmax', bounds._northEast.lng);
    }
  }, [drawnItems]);


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

  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [areaName, setAreaName] = useState('');
  const [distance, setDistance] = useState('.005');
  const [rasterBand, setRasterBand] = useState('VV');
  const [coordinates, setCoordinates] = useState(null);
  const [apiStatus, setApiStatus] = useState({});

  const sendDataToAPI = () => {
    const formattedStartDate = startDate ? format(startDate, 'yyyy-MM-dd') : null;
    const formattedEndDate = endDate ? format(endDate, 'yyyy-MM-dd') : null;
  
    // Format coordinates as four separate arguments
    const formattedCoordinates = coordinates
      ? `${coordinates.xmin} ${coordinates.ymin} ${coordinates.xmax} ${coordinates.ymax}`
      : null;
  
    const data = {
      startDate: formattedStartDate,
      endDate: formattedEndDate,
      areaName: areaName,
      distance: distance,
      rasterBand: rasterBand,
      coordinates: formattedCoordinates // Update coordinates to send formatted string
    };
  
    const apiUrl = 'http://127.0.0.1:5000/api/create';
  
    setApiStatus({ success: true, message: `Sending data to API...` });
  
    setTimeout(() => {
      fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      })
        .then(response => {
          if (!response.ok) {
            throw new Error('Network response was not successful... Please ensure all the parameters are filled out correctly');
          }
          return response.json();
        })
        .then(data => {
          setApiStatus({ success: true, message: `Data sent successfully\nServer Response: ${data.status}` });
        })
        .catch(error => {
          setApiStatus({ success: false, message: `Error: ${error.message}`+ '. Please ensure all the parameters are filled out correctly' });
        });
    }, 2000);
  };

  return (
    <>
    <div style={{background: '#272727', fontSize: '25px',
                fontFamily: 'Arial', display:'flex', 
                justifyContent:'center', paddingTop: '30px',
                paddingBottom: '15px', color: 'white'
                }}>
      <p>
        <strong>Create a new study area below!</strong>
      </p>
    </div>
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

    </div>
    <div className='container-menu-full'>
      <div className='create-text'>
      </div>
      <div style={{paddingBottom:'15px'}}>
        <label style={{paddingRight:'15px'}} htmlFor='start_date'>Start Date:</label>
        <DatePicker 
          id='start_date'
          selected={startDate}
          onChange={date => setStartDate(date)}
          dateFormat='yyyy-MM-dd'
          placeholderText='Select Start Date'
          className='inputField'
        />
        <label htmlFor='end_date'>End Date:</label>
        <DatePicker 
          id='end_date'
          selected={endDate}
          onChange={date => setEndDate(date)}
          dateFormat='yyyy-MM-dd'
          placeholderText='Select End Date'
          className='inputField'
        />
      </div>
      <div>
        <label htmlFor='area_name'>Area Name: </label>
        <input type='text' id='area_name' value={areaName} onChange={e => setAreaName(e.target.value)} className='inputField' />
      </div>
      <div style={{paddingTop:'20px'}}>
        <label htmlFor='distance'>Distance between sampling (.005 = 500 meters): </label>
        <input type='text' id='distance' value={distance} onChange={e => setDistance(e.target.value)} className='inputFieldDist' />
        <div style={{paddingTop:'15px'}}>
        <div className='radioGroup'>
          <label1 htmlFor='distance'>Choose Raster Band:</label1>
          <input type='radio' id='vv' name='raster_band' value='VV' checked={rasterBand === 'VV'} onChange={() => setRasterBand('VV')} />
          <label htmlFor='vv'>VV</label>
          <input type='radio' id='vh' name='raster_band' value='VH' checked={rasterBand === 'VH'} onChange={() => setRasterBand('VH')} />
          <label htmlFor='vh'>VH</label>
        </div>
        </div>
        <div>
          <div className='inputFieldCoordinateContainer'>
            <div className='inputFieldCoordinateWrapper'>
              <label className='inputFieldCoordinateLabel'>Ymax</label>
              <input 
                type='text' 
                value={drawnItems.length > 0 ? drawnItems[0].getBounds()._northEast.lat : ''} 
                onChange={e => updateCoordinates('ymax', e.target.value)} 
                className='inputFieldCoordinate' 
              />
            </div>
            <div className='inputFieldCoordinateWrapper'>
              <label className='inputFieldCoordinateLabel'>Xmin</label>
              <input 
                type='text' 
                value={drawnItems.length > 0 ? drawnItems[0].getBounds()._southWest.lng : ''} 
                onChange={e => updateCoordinates('xmin', e.target.value)} 
                className='inputFieldCoordinate' 
              />
            </div>
            <div className='inputFieldCoordinateWrapper'>
              <label className='inputFieldCoordinateLabel'>Ymin</label>
              <input 
                type='text' 
                value={drawnItems.length > 0 ? drawnItems[0].getBounds()._southWest.lat : ''} 
                onChange={e => updateCoordinates('ymin', e.target.value)} 
                className='inputFieldCoordinate' 
              />
            </div>
            <div className='inputFieldCoordinateWrapper'>
              <label className='inputFieldCoordinateLabel'>Xmax</label>
              <input 
                type='text' 
                value={drawnItems.length > 0 ? drawnItems[0].getBounds()._northEast.lng : ''} 
                onChange={e => updateCoordinates('xmax', e.target.value)} 
                className='inputFieldCoordinate' 
              />
            </div>
          </div>
        </div>
      </div>
      </div>
      <div style={{display:'flex', justifyContent:'center', backgroundColor:'#272727'}}>

        <button onClick={sendDataToAPI} className='submitButton'>Submit to API</button>
      </div>

      <div style={{backgroundColor:'#272727',paddingBottom: '30px', paddingTop:'25px'}}>   
        {apiStatus.message && (
        <div className={`apiMessage ${apiStatus.success ? 'success' : 'error'}`}>
            {apiStatus.message}
        </div>
        )}
      </div>
    </>
  );
}

export default CreateMenu;