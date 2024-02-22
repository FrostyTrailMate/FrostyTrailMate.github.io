import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { XYPlot, XAxis, YAxis, HorizontalGridLines, VerticalGridLines, LineSeries } from 'react-vis';
import 'react-vis/dist/style.css'; // Import the default react-vis styles
import './CCStyles/ElevationCoverageGraph.css'; // Import your custom CSS file

const ElevationCoverageGraph = () => {
    const [results, setResults] = useState([]);

    useEffect(() => {
        // Fetch data when the component mounts
        axios.get('http://127.0.0.1:5000/api/results')
            .then(response => {
                setResults(response.data);
            })
            .catch(error => {
                console.error('Error fetching results:', error);
            });
    }, []);

    // Extract coverage_percentage as x values
    const coveragePercentages = results.map(result => result.coverage_percentage);

    // Extract elevation values and parse the first number as integers
    const elevations = results.map(result => {
        const elevationRange = result.elevation.split('-'); // Split the elevation range by '-'
        return parseInt(elevationRange[0]); // Extract the first number and parse it as an integer
    });

    // Prepare data in format accepted by react-vis
    const data = coveragePercentages.map((value, index) => ({ x: value, y: elevations[index] }));

    return (
        <div className="graph-container">
            <h2 className="graph-title">Coverage Percentage vs. Elevation</h2>
            <XYPlot className="graph" xType="linear" yType="linear">
                <HorizontalGridLines />
                <VerticalGridLines />
                <XAxis title="Coverage Percentage" />
                <YAxis title="Elevation" />
                <LineSeries data={data} />
            </XYPlot>
        </div>
    );
};

export default ElevationCoverageGraph;












