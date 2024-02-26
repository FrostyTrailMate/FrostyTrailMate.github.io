import React, { useState, useEffect } from 'react';
import MapComponent from '../MapComponent';
import ResultsTable from '../ResultsTable';
import ElevationCoverageGraph from '../Graph';
import axios from 'axios';

import 'react-datepicker/dist/react-datepicker.css';
import '../CCStyles/HomeCover.css';
import '../CCStyles/Table.css';
import '../CCStyles/Graph.css';

function Home() {
  const [selectedArea, setSelectedArea] = useState('');
  const [uniqueAreaNames, setUniqueAreaNames] = useState([]);

  useEffect(() => {
    axios.get('http://127.0.0.1:5000/api/results')
      .then(response => {
        const areas = response.data.map(result => result.area_name);
        const uniqueAreas = [...new Set(areas)];
        setUniqueAreaNames(uniqueAreas);
      })
      .catch(error => {
        console.error('Error fetching results:', error);
      });
  }, []);

  return (
    <>
      <div className='homecover-container'>
        <h1> FROSTY TRAIL MATE </h1>
        <p> Explore Yosemite's Trails with Confidence </p>
        <div className="filter-container">
          <label htmlFor="areaFilter">Filter reports by area:</label>
          <select id="areaFilter" value={selectedArea} onChange={e => setSelectedArea(e.target.value)}>
            <option value="">All Areas</option>
            {uniqueAreaNames.map(area => (
              <option key={area} value={area}>{area}</option>
            ))}
          </select>
        </div>
      </div>
      <MapComponent />
      <ResultsTable selectedArea={selectedArea} />
      <ElevationCoverageGraph selectedArea={selectedArea} />
    </>
  );
}

export default Home;
