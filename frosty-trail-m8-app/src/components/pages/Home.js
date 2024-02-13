import React from 'react';
import MapComponent from '../MapComponent';
import ResultsTable from '../ResultsTable';
import Calendar from '../Calendar';
import 'react-datepicker/dist/react-datepicker.css';
import '../CCStyles/HomeCover.css';
import '../CCStyles/Table.css';
import '../CCStyles/Calendar.css';

function Home() {
  return (
    <>
    <div className='homecover-container'>
      <h1> FROSTY TRAIL MATE </h1>
      <p> Explore Yosemite's Trails with Confidence </p>
    </div>
      <MapComponent />
      <Calendar />
      <ResultsTable />
    </>
  );
}

export default Home;
