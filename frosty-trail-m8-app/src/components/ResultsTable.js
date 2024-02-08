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

    return (
        <div>
            <h1>Results Displayed</h1>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Altitude</th>
                        <th>Snow Cover</th>
                        <th>Area</th>
                    </tr>
                </thead>
                <tbody>
                    {results.map(result => (
                        <tr key={result.id_res}>
                            <td>{result.id_res}</td>
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

