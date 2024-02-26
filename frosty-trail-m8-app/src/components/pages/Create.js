import React, { useState } from 'react';
import '../CCStyles/Create.css';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { format } from 'date-fns';

function Create() {
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
  
    setApiStatus({ success: true, message: `Sending data to: ${apiUrl}` });
  
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
            throw new Error('Network response was not ok');
          }
          return response.json();
        })
        .then(data => {
          setApiStatus({ success: true, message: `Data sent successfully\nServer Response: ${data.status}` });
        })
        .catch(error => {
          setApiStatus({ success: false, message: `Error: ${error.message}` });
        });
    }, 2000);
  };
  

  const updateCoordinates = (key, value) => {
    setCoordinates(prevCoordinates => ({
      ...prevCoordinates,
      [key]: value
    }));
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
        <label htmlFor='distance'>Distance between sampling (.005 = 500 meters): </label>
        <input type='text' id='distance' value={distance} onChange={e => setDistance(e.target.value)} className='inputFieldDist' />
        <div>
          <label>Choose Raster Band:</label>
        </div>
        <div className='radioGroup'>
          <input type='radio' id='vv' name='raster_band' value='VV' checked={rasterBand === 'VV'} onChange={() => setRasterBand('VV')} />
          <label htmlFor='vv'>VV</label>
          <input type='radio' id='vh' name='raster_band' value='VH' checked={rasterBand === 'VH'} onChange={() => setRasterBand('VH')} />
          <label htmlFor='vh'>VH</label>
        </div>
        <div>
          <label>Enter Coordinates:</label>
        </div>
        <div className='inputFieldCoordinateContainer'>
          <div className='inputFieldCoordinateWrapper'>
            <label className='inputFieldCoordinateLabel'>Ymax</label>
            <input type='text' value={coordinates ? coordinates.ymax : ''} onChange={e => updateCoordinates('ymax', e.target.value)} className='inputFieldCoordinate' />
          </div>
          <div className='inputFieldCoordinateWrapper'>
            <label className='inputFieldCoordinateLabel'>Xmin</label>
            <input type='text' value={coordinates ? coordinates.xmin : ''} onChange={e => updateCoordinates('xmin', e.target.value)} className='inputFieldCoordinate' />
          </div>
        </div>
        <div className='inputFieldCoordinateContainer'>
          <div className='inputFieldCoordinateWrapper'>
            <label className='inputFieldCoordinateLabel'>Ymin</label>
            <input type='text' value={coordinates ? coordinates.ymin : ''} onChange={e => updateCoordinates('ymin', e.target.value)} className='inputFieldCoordinate' />
          </div>
          <div className='inputFieldCoordinateWrapper'>
            <label className='inputFieldCoordinateLabel'>Xmax</label>
            <input type='text' value={coordinates ? coordinates.xmax : ''} onChange={e => updateCoordinates('xmax', e.target.value)} className='inputFieldCoordinate' />
          </div>
        </div>

        <button onClick={sendDataToAPI} className='submitButton'>Send Data to API</button>

      </div>
      {coordinates && (
        <div className='coordinates'>
          <p>xmin: {coordinates.xmin}</p>
          <p>ymin: {coordinates.ymin}</p>
          <p>xmax: {coordinates.xmax}</p>
          <p>ymax: {coordinates.ymax}</p>
        </div>
      )}
      {apiStatus.message && (
        <div className={`apiMessage ${apiStatus.success ? 'success' : 'error'}`}>
          {apiStatus.message}
        </div>
      )}
    </>
  );
}

export default Create;
