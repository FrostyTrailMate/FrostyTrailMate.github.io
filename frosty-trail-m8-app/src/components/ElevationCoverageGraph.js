import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { XYPlot, XAxis, YAxis, HorizontalGridLines, VerticalGridLines, LineSeries } from 'react-vis';
import "react-vis/dist/style.css";
import './CCStyles/ElevationCoverageGraph.css'; // Import the graph component

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

    // Calculate trend line
    const trendLineData = calculateTrendLine(data);

    // Function to calculate trend line

    function calculateTrendLine(data) {
        // Simple linear regression
        let xSum = 0;
        let ySum = 0;
        let xySum = 0;
        let xSquaredSum = 0;
        const n = data.length;
    
        for (let i = 0; i < n; i++) {
            xSum += data[i].x;
            ySum += data[i].y;
            xySum += data[i].x * data[i].y;
            xSquaredSum += Math.pow(data[i].x, 2);
        }
    
        const m = (n * xySum - xSum * ySum) / (n * xSquaredSum - Math.pow(xSum, 2));
        const b = (ySum - m * xSum) / n;
    
        // Generate trend line data
        const trendLineData = [];
        for (let i = 0; i < n; i++) {
            trendLineData.push({ x: data[i].x, y: m * data[i].x + b });
        }
    
        return trendLineData;
    }

    return (
        <div className="graph-container-dark">
            <div className="graph-title-dark">Elevation VS Snow Coverage </div>
            <XYPlot className="react-vis-xy-plot-dark" width={1000} height={400} xType="linear" yType="linear">
                <HorizontalGridLines />
                <VerticalGridLines />
                <XAxis title="Elevation (m)" style={{ title: { fill: '#fff', fontFamily: 'Arial, sans-serif', fontSize: '14px' } }} />
                <YAxis title="Coverage Percentage (%)" style={{ title: { fill: '#fff', fontFamily: 'Arial, sans-serif', fontSize: '14px' } }} />
                <LineSeries data={data} stroke="rgba(0, 255, 255, 0.971)" strokeWidth={4} />
                <LineSeries data={trendLineData} stroke="#fff" strokeWidth={2} strokeDasharray="5,5" />
            </XYPlot>
        </div>
    );
};

export default ElevationCoverageGraph;














