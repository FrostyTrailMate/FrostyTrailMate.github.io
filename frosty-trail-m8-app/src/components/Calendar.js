import React, { useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import './CCStyles/Calendar.css'; // Import CSS for styling

const Calendar = ({ onDateChange }) => {
  const [selectedDate, setSelectedDate] = useState(null);

  const handleDateChange = (date) => {
    setSelectedDate(date);
    // Pass the selected date to the parent component
    onDateChange(date);
  };

  return (
    <div className="calendar-container">
      <DatePicker
        selected={selectedDate}
        onChange={handleDateChange}
        dateFormat="yyyy-MM-dd"
      />
    </div>
  );
};

export default Calendar;

