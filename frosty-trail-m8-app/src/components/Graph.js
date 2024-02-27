import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { XYPlot, XAxis, YAxis, HorizontalGridLines, VerticalGridLines, LineSeries, MarkSeries, Crosshair } from 'react-vis';
import "react-vis/dist/style.css";
import './CSStyles/Graph.css'; // Import the graph component

const ElevationCoverageGraph = ({ selectedArea }) => {
    const [results, setResults] = useState([]);
    const [crosshairValues, setCrosshairValues] = useState([]);

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

    // Filter results based on selected area
    const filteredResults = selectedArea ? results.filter(result => result.area_name === selectedArea) : results;

    // Extract elevation as x values
    const elevations = filteredResults.map(result => {
        const elevationRange = result.elevation.split('-'); // Split the elevation range by '-'
        return parseInt(elevationRange[0]); // Extract the first number and parse it as an integer
    });

    // Extract coverage_percentage as y values
    const coveragePercentages = filteredResults.map(result => result.coverage_percentage);

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

    // Event handler for crosshair
    function onMouseLeave() {
        setCrosshairValues([]);
    }

    function onNearestX(value) {
        const { x, y } = value;
        setCrosshairValues([{ x, y }]);
    }

    return (
        <div className="graph-container-dark">
                <div className="graph-title-dark"><strong>ELEVATION VS SNOW COVERAGE (%)</strong></div>
                <XYPlot className="react-vis-xy-plot-dark" 
                    width={1200} height={450} xType="linear" yType="linear" 
                    style={{background: '#444', borderRadius: '10px'}} onMouseLeave={onMouseLeave}>
                <HorizontalGridLines style={{ stroke: 'rgba(255, 255, 255, 0.3)', strokeWidth: 1 }} />
                <VerticalGridLines style={{ stroke: 'rgba(255, 255, 255, 0.3)', strokeWidth: 1 }}/>
                <XAxis 
                    title="Elevation (m)" style={{ title: { fill: '#fff', fontFamily: 'Arial, sans-serif', fontSize: '16px'},
                    line: { stroke: '#fff', strokeWidth: 1}}} />
                <YAxis 
                    title="Coverage Percentage (%)" style={{ title: { fill: '#fff', fontFamily: 'Arial, sans-serif', fontSize: '16px' },
                    line: { stroke: '#fff', strokeWidth: 1}}} />
                <LineSeries data={data} stroke="rgba(0, 255, 255, 0.971)" strokeWidth={4} onNearestX={onNearestX} />
                <LineSeries data={trendLineData} stroke="#e9e9e9" strokeWidth={2} strokeDasharray="10" />
                <MarkSeries data={data} size={6} color="rgba(0, 255, 255, 0.971)" stroke="#fff" strokeWidth={2}/>
                <Crosshair 
                    values={crosshairValues} 
                    titleFormat={(values) => {
                        return {
                            title: <span style={{ fontWeight: 'bold', fontSize: '14px'}}>Elevation</span>,
                            value: <span style={{ fontWeight: 'bold',fontSize: '14px' }}>{values[0]?.x} m</span> // Make the x-value bold
                        };
                    }}
                    itemsFormat={(values) => {
                        return values.map((v) => {
                            if (v) {
                                return {
                                    value: <span style={{ fontWeight: 'bold',fontSize: '14px'}}>{v.y} %</span>, // Make the y-value bold
                                    title: <span style={{ fontWeight: 'bold',fontSize: '14px'}}>Snow Coverage</span> 
                                };
                            }
                            return null;
                        });
                }}/>
                </XYPlot >
        </div>
    );
};

export default ElevationCoverageGraph;
