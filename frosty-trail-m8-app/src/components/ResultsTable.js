import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ResultsTable = () => {
    const [results, setResults] = useState([]);

    useEffect(() => {
        axios.get('http://127.0.0.1:5000/api/results')
            .then(response => {
                setResults(response.data);
            })
            .catch(error => {
                console.error('Error fetching results:', error);
            });
    }, []);
/*
    // Function to format date to only include day, month, and year of the date field
    const formatDate = (dateString) => {
        const date = new Date(dateString);
        const day = date.getDate();
        const month = date.toLocaleString('default', { month: 'short' }).charAt(0).toUpperCase() + date.toLocaleString('default', { month: 'short' }).slice(1);
        const year = date.getFullYear();
        return `${day} ${month} ${year}`;
    };*/

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
        const csvContent = convertToCSV(results);
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
                        {results
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
            <button className="download-btn" onClick={downloadCSV}>Download Table as CSV</button>
        </div>
    );
    
};

export default ResultsTable;


