import React from 'react';

const Popup = ({ message, onConfirm, onCancel }) => {
  return (
    <div className="popup-container">
      <div className="popup">
        <div className="popup-content">
          <p>{message}</p>
          <div className="button-container-pop">
            <button onClick={onConfirm}>Yes</button>
            <button onClick={onCancel}>No</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Popup;
