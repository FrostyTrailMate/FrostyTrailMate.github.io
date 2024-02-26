import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ResultsTable = ({ selectedArea }) => {
    const [results, setResults] = useState([]);
    const [areaGeneratedDateTime, setAreaGeneratedDateTime] = useState(null);

    useEffect(() => {
        axios.get('http://127.0.0.1:5000/api/results')
            .then(response => {
                setResults(response.data);
                if (selectedArea) {
                    const filteredResult = response.data.find(result => result.area_name === selectedArea);
                    if (filteredResult) {
                        setAreaGeneratedDateTime(filteredResult.datetime);
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching results:', error);
            });
    }, [selectedArea]);

    const filteredResults = selectedArea ? results.filter(result => result.area_name === selectedArea) : results;

    // Function to convert results data to CSV format
    const convertToCSV = (data) => {
        const csvRows = [];
        const headers = Object.keys(data[0]);
        csvRows.push(headers.join(','));

        for (const row of data) {
            const values = headers.map(header => {
                const escaped = ('' + row[header]).replace(/"/g, '\\"');
                return `"${escaped}"`;
            });
            csvRows.push(values.join(','));
        }

        return csvRows.join('\n');
    };

    // Function to trigger download of CSV file
    const downloadCSV = () => {
        const csvContent = convertToCSV(filteredResults);
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'results.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    };

    return (
        <div className="tablecontainer">
            <div className="scrollable-table">
                <table className="styled-table">
                    <thead>
                        <tr>
                            <th> AREA </th>
                            <th> ELEVATION (m) </th>
                            <th> DETECTED POINTS </th>
                            <th> TOTAL POINTS </th>
                            <th> SNOW COVERAGE (%) </th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredResults
                            .sort((a, b) => {
                                // Extract the first number from the string value of elevation
                                const firstNumberA = parseInt(a.elevation.match(/\d+/)[0]);
                                const firstNumberB = parseInt(b.elevation.match(/\d+/)[0]);
                                
                                // Compare the first numbers in reverse order for sorting from higher to lower
                                return firstNumberB - firstNumberA;
                            })
                            .map(result => (
                                <tr key={result.id_res}>
                                    <td>{result.area_name}</td>
                                    <td>{result.elevation}</td>
                                    <td>{result.detected_points}</td>
                                    <td>{result.total_points}</td>
                                    <td>{result.coverage_percentage}</td>
                                </tr>
                            ))}
                    </tbody>
                </table>
            </div>
            {areaGeneratedDateTime && (
                <div className = "message-container">
                    Custom area {selectedArea} was generated on {areaGeneratedDateTime}.
                </div>
            )}
            <button className="download-btn" onClick={downloadCSV}>Download Table as CSV</button>
        </div>
    );
};

export default ResultsTable;
