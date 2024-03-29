import React, { useState, useEffect } from 'react';
import MapComponent from '../MapComponent';
import ResultsTable from '../ResultsTable';
import ElevationCoverageGraph from '../Graph';
import axios from 'axios';

import 'react-datepicker/dist/react-datepicker.css';
import '../CSStyles/Results.css';
import '../CSStyles/Table.css';
import '../CSStyles/Graph.css';

function Results() {
  const [selectedArea, setSelectedArea] = useState(null); // Change to null
  const [uniqueAreaNames, setUniqueAreaNames] = useState([]);
  

  useEffect(() => {
    axios.get('http://127.0.0.1:5000/api/results')
      .then(response => {
        const sortedData = response.data.sort((a, b) => a.id - b.id); // Sort by id
        const areas = sortedData.map(result => result.area_name);
        const uniqueAreas = [...new Set(areas)];
        setUniqueAreaNames(uniqueAreas);
        if (uniqueAreas.length > 0) {
          setSelectedArea(uniqueAreas[uniqueAreas.length - 1]); // Select the last area
        }
      })
      .catch(error => {
        console.error('Error fetching results:', error);
      });
  }, []);
  

  return (
    <>
      <div className="filter-container">
          <label style={{fontSize: '20px', fontFamily:'Arial'}}
                htmlFor="areaFilter">Filter reports by area:</label>
          <select id="areaFilter" value={selectedArea} onChange={e => setSelectedArea(e.target.value)}>
            {uniqueAreaNames.map(area => (
              <option key={area} value={area}>{area}</option>
            ))}
          </select>
      </div>
      <MapComponent selectedArea={selectedArea} />
      <ResultsTable selectedArea={selectedArea} />
      <ElevationCoverageGraph selectedArea={selectedArea} />
    </>
  );
}

export default Results;
