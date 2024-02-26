import React, { useEffect, useState } from 'react';
import '../CCStyles/Create.css';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import axios from 'axios';


function Create() {
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [areaName, setAreaName] = useState('');
  const [distance, setDistance] = useState('');
  const [rasterBand, setRasterBand] = useState('VV');
  const [coordinates, setCoordinates] = useState(null);
  const [apiStatus, setApiStatus] = useState({});

  const sendDataToAPI = () => {
    const data = {
      startDate: startDate,
      endDate: endDate,
      areaName: areaName,
      distance: distance,
      rasterBand: rasterBand,
    };

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
