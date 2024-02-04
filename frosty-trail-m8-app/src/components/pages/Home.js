import React from 'react';
import '../../App.css';
import MapComponent from '../MapComponent';

function Home() {
  return (
    <>
    <div className='hero-container'>
      <h1> FROSTY TRAIL MATE </h1>
      <p> Explore Yosemite's Trails with Confidence </p>
    </div>
      <MapComponent />
    </>
  );
}

export default Home;