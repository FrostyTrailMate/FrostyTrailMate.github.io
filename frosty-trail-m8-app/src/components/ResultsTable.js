import React, { useState, useEffect } from 'react';

const ResultsTable = () => {
    const [results, setResults] = useState([]);

    useEffect(() => {
        // Fetch data from Flask backend
        fetch('/api/results')
            .then(response => response.json())
            .then(data => {
                setResults(data); // Update state with the fetched data
            })
            .catch(error => {
                console.error('Error fetching results:', error);
            });
    }, []);

    return (
        <div>
            <h1>Results Displayed</h1>
            <table>
                <thead>
                    <tr>
                        <th>Altitude</th>
                        <th>Snow Cover</th>
                        <th>Area</th>
                    </tr>
                </thead>
                <tbody>
                    {results.map(result => (
                        <tr key={result.id_res}>
                            <td>{result.altitude}</td>
                            <td>{result.snowcover}</td>
                            <td>{result.darea}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default ResultsTable;

