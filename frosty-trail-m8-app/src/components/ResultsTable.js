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
        <div className="tablecontainer">
            <div className="scrollable-table">
                <table className="styled-table">
                    <thead>
                        <tr>
                            <th> AREA </th>
                            <th> ELEVATION </th>
                            <th> SNOW COVERAGE (%) </th>
                            <th> DATE </th>
                        </tr>
                    </thead>
                    <tbody>
                        {results.map(result => (
                            <tr 
                                key={result.id_res}>
                                <td>{result.area_name}</td>
                                <td>{result.elevation}</td>
                                <td>{result.coverage_percentage}</td>
                                <td>{result.ddatetime}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ResultsTable;




