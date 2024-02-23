import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { XYPlot, XAxis, YAxis, HorizontalGridLines, VerticalGridLines, LineSeries } from 'react-vis';
import 'react-vis/dist/style.css';
import './CCStyles/ElevationCoverageGraph.css';

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

    // Extract elevation as x values
    const elevations = results.map(result => {
        const elevationRange = result.elevation.split('-'); // Split the elevation range by '-'
        return parseInt(elevationRange[0]); // Extract the first number and parse it as an integer
    });

    // Extract coverage_percentage as y values
    const coveragePercentages = results.map(result => result.coverage_percentage);

    // Prepare data in format accepted by react-vis
    const data = elevations.map((value, index) => ({ x: value, y: coveragePercentages[index] }));

    return (
        <div className="graph-container">
            <XYPlot width={600} height={400} xType="linear" yType="linear">
                <HorizontalGridLines />
                <VerticalGridLines />
                <XAxis title="Elevation" />
                <YAxis title="Coverage Percentage" />
                <LineSeries data={data} />
            </XYPlot>
        </div>
    );
};

export default ElevationCoverageGraph;











