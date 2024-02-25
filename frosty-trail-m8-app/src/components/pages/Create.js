<<<<<<< Updated upstream
import React from 'react';
import '../CCStyles/Create.css';

function Create() {
  return (
    <>
      <div className='Create'>
        <p><strong></strong>
        </p>
      </div>
    </>
  );
}

export default Create;


/*// Create elements
const homecoverContainer = document.createElement('div');
homecoverContainer.className = 'homecover-container';
const h1 = document.createElement('h1');
h1.textContent = 'FROSTY TRAIL MATE';
const p = document.createElement('p');
p.textContent = 'Explore Trails with Confidence';
homecoverContainer.appendChild(h1);
homecoverContainer.appendChild(p);
document.body.appendChild(homecoverContainer);
=======
import React, { useEffect, useState } from 'react';
import '../CCStyles/Create.css';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import axios from 'axios';
import { MapContainer, TileLayer, Rectangle, useMapEvents, FeatureGroup, DrawControl } from 'react-leaflet'; 
import 'leaflet-draw';
import 'leaflet-draw/dist/leaflet.draw.css';
>>>>>>> Stashed changes


function Create() {
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [areaName, setAreaName] = useState('');
  const [distance, setDistance] = useState('');
  const [rasterBand, setRasterBand] = useState('VV');
  const [coordinates, setCoordinates] = useState(null);
  const [apiStatus, setApiStatus] = useState({});

  // State to store rectangle bounds
  const [rectangleBounds, setRectangleBounds] = useState(null);

  // Leaflet 'useMapEvents' hook to interact with map
  function AddRectangleToMap() {
    const map = useMapEvents({
      click() {
        setRectangleBounds(null); // Reset on click
      },
      draw: (event) => {
        switch (event.layerType) {
          case 'rectangle':
            setRectangleBounds(event.layer.getBounds());
            break;
          default:
            break; // Do nothing for other draw types
        }
      },
    });

    return rectangleBounds ? (
      <Rectangle bounds={rectangleBounds} pathOptions={{ color: 'blue' }} />
    ) : null;
  }

  const sendDataToAPI = () => {
    const data = {
      startDate: startDate,
      endDate: endDate,
      areaName: areaName,
      distance: distance,
      rasterBand: rasterBand,
    };

    // Include coordinates from rectangleBounds
    if (rectangleBounds) {
      data.xmin = rectangleBounds.getSouthWest().lng;
      data.ymin = rectangleBounds.getSouthWest().lat;
      data.xmax = rectangleBounds.getNorthEast().lng;
      data.ymax = rectangleBounds.getNorthEast().lat;
    }

    axios.post('http://127.0.0.1:5000/api/create', data)
      .then(response => {
        setApiStatus({ success: true, message: 'Data sent successfully' });
      })
      .catch(error => {
        if (error.response) {
          setApiStatus({ success: false, message: 'Server error: ' + error.response.status });
        } else if (error.request) {
          setApiStatus({ success: false, message: 'No response from server' });
        } else {
          setApiStatus({ success: false, message: 'Error: ' + error.message });
        }
      });
  };

  return (
    <>
      <div className='Create'>
        <p>
          <strong>Create a new study area below!</strong>
        </p>
      </div>
      <div>
        <label htmlFor='start_date'>Start Date:</label>
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
      <div>
        <label htmlFor='distance'>Distance between sampling points (.005 = 500 meters): </label>
        <input type='text' id='distance' value={distance} onChange={e => setDistance(e.target.value)} className='inputFieldDist' />
      </div>
      <div>
        <label>Choose Raster Band:</label>
      </div>
      <div className='radioGroup'>
        <input type='radio' id='vv' name='raster_band' value='VV' checked={rasterBand === 'VV'} onChange={() => setRasterBand('VV')} />
        <label htmlFor='vv'>VV</label>
        <input type='radio' id='vh' name='raster_band' value='VH' checked={rasterBand === 'VH'} onChange={() => setRasterBand('VH')} />
        <label htmlFor='vh'>VH</label> 
      </div>

      {/* Leaflet Map Section */}
      <div className='leaflet-container'>
      <MapContainer center={[51.505, -0.09]} zoom={13}> 
        <TileLayer
          // ... your tile layer setup
        />
        <FeatureGroup> {/* A FeatureGroup is needed for Draw controls */}
          <DrawControl 
            position='topright'
            onCreated={(e) => {
              const type = e.layerType;
              if (type === 'rectangle') {
                setRectangleBounds(e.layer.getBounds());
              }
            }} 
            draw={{
              rectangle: true, // Enable rectangle drawing (you can add more options if needed)
              circle: false,  // Disable other drawing tools here 
              polyline: false,
              // ... etc 
            }}
          />
        </FeatureGroup>
        <AddRectangleToMap /> 
      </MapContainer>
      </div>

      <button onClick={sendDataToAPI} className='submitButton'>Send Data to API</button>
      {/* ... (the rest of your component: coordinates display, apiStatus message) */}
    </>
  );
}

<<<<<<< Updated upstream
document.getElementById('area_name').addEventListener('input', function() {
  const areaName = this.value;
  console.log("Area Name:", areaName);
});

document.getElementById('distance').addEventListener('input', function() {
  const distance = this.value;
  console.log("Distance:", distance);
});

document.querySelectorAll('input[name="raster_band"]').forEach(function(radio) {
  radio.addEventListener('change', function() {
    const rasterBand = this.value;
    console.log("Raster Band:", rasterBand);
  });
});
*/
=======
export default Create;
>>>>>>> Stashed changes
