import { MapContainer, TileLayer,FeatureGroup} from 'react-leaflet';
import L from 'leaflet';
import React, { useState, useEffect, useRef } from 'react';
import DatePicker from 'react-datepicker';
import { format } from 'date-fns';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import { EditControl } from 'react-leaflet-draw';
import Popup from '../Popup';
import '../CSStyles/Create.css'
import 'react-datepicker/dist/react-datepicker.css';

function Create() {

  const [basemap, setBasemap] = useState('stamenTerrain');
  const [drawnItems, setDrawnItems] = useState([]);
  const drawControlRef = useRef(null);
  const [showPopup, setShowPopup] = useState(false);
  const [popupMessage, setPopupMessage] = useState('');
  const [resetSuccess, setResetSuccess] = useState(false);
  const [areaNameError, setAreaNameError] = useState();

  const Tooltip = ({ text, children }) => {
    const [showTooltip, setShowTooltip] = useState(false);

    return (
      <div className="tooltip-container">
        <div
          className="tooltip-icon"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          ?
        </div>
        {showTooltip && <div className="tooltip-text">{text}</div>}
        {children}
      </div>
    );
  };

  const togglePopup = () => {
    setShowPopup(!showPopup);
  };

  const resetDatabase = () => {
    setPopupMessage('Are you sure you want to reset the database?');
    togglePopup();
  };

  const handleResetCancellation = () => {
    togglePopup(); 
  };
  
  const updateCoordinates = (key, value) => {
    setCoordinates(prevCoordinates => ({
      ...prevCoordinates,
      [key]: value
    }));
  };

  const handleResetConfirmation = () => {
    fetch('http://127.0.0.1:5000/api/reset', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to reset database');
        }
        return response.json();
      })
      .then(data => {
        console.log('Resetting database...');
        togglePopup();
        setResetSuccess(true); // Set reset success to true after successful reset
        setTimeout(() => {
          setResetSuccess(false); // Reset the success message after a certain delay
        }, 5000); // Adjust delay as needed
      })
      .catch(error => {
        console.error('Error resetting database:', error);
      });
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

  const handleAreaNameChange = (value) => {
    if (/^[a-zA-Z0-9]*$/.test(value)) {
      setAreaName(value);
      setAreaNameError('');
    } else {
      setAreaNameError('Special characters and spaces are not allowed');
    }
  };

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

  const handleDrawCreated = (e) => {
    const layer = e.layer;
    setDrawnItems([layer]);
  };

  const handleDrawDeleted = () => {
    setDrawnItems([]);
  };

  const handleDrawEdited = (e) => {
    const layers = e.layers;
    const editedItems = layers.getLayers();
    setDrawnItems([...editedItems]);
  };

  const sixDaysAgo = new Date();
  sixDaysAgo.setDate(sixDaysAgo.getDate() - 6);

  const [startDate, setStartDate] = useState(sixDaysAgo);
  const [endDate, setEndDate] = useState(new Date());
  const [areaName, setAreaName] = useState('');
  const [distance, setDistance] = useState('500');
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
  
    setApiStatus({ success: true, message: `Sending data to API. Please wait for a successful response.` });
  
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
          setApiStatus({ success: true, message: `Data sent successfully! Please check the Results page.` });
        })
        .catch(error => {
          setApiStatus({ success: false, message: `Error: ${error.message}. Please ensure all the parameters are filled out correctly` });
        });
    }, 2000);
  };

  const calculateArea = () => {
    if (drawnItems.length > 0) {
      const area = L.GeometryUtil.geodesicArea(drawnItems[0].getLatLngs()[0]);
      return area.toFixed(2); // Return area rounded to 2 decimal places
    }
    return 0; // Return 0 if no polygon is drawn
  };
  
  
  return (
    <>
      <div className='homecover-container-menu'>
        <h1> FROSTY TRAIL MATE </h1>
        <p> Explore Trails with Confidence </p>
      </div>
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
          <Tooltip text="Select a basemap. Has no effect on the program.">
            <strong>Select your Basemap:</strong>
          </Tooltip>
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
              rectangle: true,
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
    <div>
    <div style={{ transform: 'translate(0%, 20%)'}}><Tooltip style={{ transform: 'translate(120%, 25%)'}}
         text="Select the coordinates by drawing a rectangle on the map above."></Tooltip>
    </div>
          <div className='inputFieldCoordinateContainer'>
            <div className='inputFieldCoordinateWrapper'>
              <label style={{paddingBottom:'10px'}} className='inputFieldCoordinateLabel'>North Coordinate</label>
              <input 
                type='text' 
                value={drawnItems.length > 0 ? drawnItems[0].getBounds()._northEast.lat : ''} 
                onChange={e => updateCoordinates('ymax', e.target.value)} 
                className='inputFieldCoordinate'
              />
            </div>
              <div className='inputFieldCoordinateWrapper'>
              <label style={{paddingBottom:'10px'}}
                className='inputFieldCoordinateLabel'>West Coordinate</label>
              <input 
                type='text' 
                value={drawnItems.length > 0 ? drawnItems[0].getBounds()._southWest.lng : ''} 
                onChange={e => updateCoordinates('xmin', e.target.value)} 
                className='inputFieldCoordinate' 
              />
            </div>
            <div className='inputFieldCoordinateWrapper'>
              <label style={{paddingBottom:'10px'}}
                className='inputFieldCoordinateLabel'>South Coordinate</label>
              <input 
                type='text' 
                value={drawnItems.length > 0 ? drawnItems[0].getBounds()._southWest.lat : ''} 
                onChange={e => updateCoordinates('ymin', e.target.value)} 
                className='inputFieldCoordinate' 
              />
            </div>
            <div className='inputFieldCoordinateWrapper'>
              <label style={{paddingBottom:'10px'}}
                className='inputFieldCoordinateLabel'>East Coordinate</label>
              <input 
                type='text' 
                value={drawnItems.length > 0 ? drawnItems[0].getBounds()._northEast.lng : ''} 
                onChange={e => updateCoordinates('xmax', e.target.value)} 
                className='inputFieldCoordinate' 
              />
            </div>
          </div>
        </div>
      <div className='create-text'>
      </div>
      <Tooltip text="Select the coordinates by drawing a rectangle on the map above."></Tooltip>
      <div style={{paddingBottom:'20px'}}>
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
      <Tooltip text="Select the coordinates by drawing a rectangle on the map above."></Tooltip>
        <label htmlFor='area_name'>Area Name: </label>
        <input type='text' id='area_name' value={areaName} onChange={e => handleAreaNameChange(e.target.value)} className='inputField' />
        {areaNameError && <p style={{ color: 'red', paddingLeft:'90px' }}>{areaNameError}</p>}
      </div>
      <div style={{paddingTop:'15px'}}>
      <div style={{paddingBottom:'10px'}}>
      <Tooltip text="Select the coordinates by drawing a rectangle on the map above."></Tooltip>
          <label htmlFor='distance'>Distance between sampling points (Meters): </label>
          <input type='text' id='distance' value={distance} onChange={e => setDistance(e.target.value)} className='inputFieldDist' />
          {calculateArea() !== 0 && (
          <label style={{borderRadius:'10px', fontSize: '18px', color: 'white',paddingRight: '20px', paddingLeft: '20px', marginRight: '20px',
                         backgroundColor:'#bc75ff',padding:'11px'}} htmlFor='area_name'> 
            Sampling Points Expected &nbsp; ≈ &nbsp;<strong>{Math.round(calculateArea() / (distance * distance))}&nbsp;</strong>
          </label>
        )}
      </div>
        <div style={{paddingTop:'10px',paddingBottom:'10px'}}>
        <div className='radioGroup'>
        <Tooltip text="Select the coordinates by drawing a rectangle on the map above."></Tooltip>
          <label1 htmlFor='distance'>Choose Raster Band:</label1>
          <input style={{position:'relative', top:'6px'}}
            type='radio' id='vv' name='raster_band' value='VV' checked={rasterBand === 'VV'} onChange={() => setRasterBand('VV')} />
          <label htmlFor='vv'>VV</label>
          <input style={{position:'relative', top:'6px'}}
            type='radio' id='vh' name='raster_band' value='VH' checked={rasterBand === 'VH'} onChange={() => setRasterBand('VH')} />
          <label htmlFor='vh'>VH</label>
        </div>
        </div>
      </div>
      </div>
      <div style={{display:'flex', justifyContent:'center', backgroundColor:'#272727',paddingBottom: '20px'}}>
        <button onClick={sendDataToAPI} className='submitButton'>Submit to API</button>
        <button onClick={resetDatabase} className='resetButton'>Reset Database</button>
      </div>
      <div style={{backgroundColor:'#272727',paddingBottom: '30px'}}>
        {showPopup && (
          <div>
          <Popup
            message={popupMessage}
            onConfirm={handleResetConfirmation}
            onCancel={handleResetCancellation}
          />
          </div>
        )}
        {resetSuccess && (
          <div className="successMessage">
            Database reset successfully!
          </div>
      )}
        </div>
      <div style={{backgroundColor:'#272727',paddingBottom: '30px'}}>   
        {apiStatus.message && (
        <div className={`apiMessage ${apiStatus.success ? 'success' : 'error'}`}>
            {apiStatus.message}
        </div>
        )}
      </div>

    </>
  );
}

export default Create;