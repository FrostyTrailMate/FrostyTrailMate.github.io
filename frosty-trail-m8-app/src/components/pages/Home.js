import React from 'react';
import MapComponent from '../MapComponent';
import ResultsTable from '../ResultsTable';
import '../CCStyles/HomeCover.css';
import '../CCStyles/Table.css';

function Home() {
  return (
    <>
    <div className='homecover-container'>
      <h1> FROSTY TRAIL MATE </h1>
      <p> Explore Yosemite's Trails with Confidence </p>
    </div>
      <MapComponent /> 
      <ResultsTable />
    </>
  );
}

export default Home;