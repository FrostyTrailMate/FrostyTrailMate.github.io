import React from 'react';
import '../CCStyles/Create.css';

function Create() {
  return (
    <>
      <div className='Create'>
        <p><strong></strong>
        </p>
      </div>
    </>
  );
}

export default Create;


/*// Create elements
const homecoverContainer = document.createElement('div');
homecoverContainer.className = 'homecover-container';
const h1 = document.createElement('h1');
h1.textContent = 'FROSTY TRAIL MATE';
const p = document.createElement('p');
p.textContent = 'Explore Trails with Confidence';
homecoverContainer.appendChild(h1);
homecoverContainer.appendChild(p);
document.body.appendChild(homecoverContainer);

const mapDiv = document.createElement('div');
mapDiv.id = 'map';
document.body.appendChild(mapDiv);

const startDateLabel = document.createElement('label');
startDateLabel.htmlFor = 'start_date';
startDateLabel.textContent = 'Start Date:';
const startDateInput = document.createElement('input');
startDateInput.type = 'text';
startDateInput.id = 'start_date';
startDateInput.placeholder = 'Select Start Date';
document.body.appendChild(startDateLabel);
document.body.appendChild(startDateInput);

const endDateLabel = document.createElement('label');
endDateLabel.htmlFor = 'end_date';
endDateLabel.textContent = 'End Date:';
const endDateInput = document.createElement('input');
endDateInput.type = 'text';
endDateInput.id = 'end_date';
endDateInput.placeholder = 'Select End Date';
document.body.appendChild(endDateLabel);
document.body.appendChild(endDateInput);

const areaNameLabel = document.createElement('label');
areaNameLabel.htmlFor = 'area_name';
areaNameLabel.textContent = 'Area Name:';
const areaNameInput = document.createElement('input');
areaNameInput.type = 'text';
areaNameInput.id = 'area_name';
document.body.appendChild(areaNameLabel);
document.body.appendChild(areaNameInput);

const distanceLabel = document.createElement('label');
distanceLabel.htmlFor = 'distance';
distanceLabel.textContent = 'Distance:';
const distanceInput = document.createElement('input');
distanceInput.type = 'text';
distanceInput.id = 'distance';
document.body.appendChild(distanceLabel);
document.body.appendChild(distanceInput);

const rasterBandLabel = document.createElement('label');
rasterBandLabel.textContent = 'Choose Raster Band:';
const vvInput = document.createElement('input');
vvInput.type = 'radio';
vvInput.id = 'vv';
vvInput.name = 'raster_band';
vvInput.value = 'VV';
vvInput.checked = true;
const vvInputLabel = document.createElement('label');
vvInputLabel.htmlFor = 'vv';
vvInputLabel.textContent = 'VV';
const vhInput = document.createElement('input');
vhInput.type = 'radio';
vhInput.id = 'vh';
vhInput.name = 'raster_band';
vhInput.value = 'VH';
const vhInputLabel = document.createElement('label');
vhInputLabel.htmlFor = 'vh';
vhInputLabel.textContent = 'VH';
document.body.appendChild(rasterBandLabel);
document.body.appendChild(vvInput);
document.body.appendChild(vvInputLabel);
document.body.appendChild(vhInput);
document.body.appendChild(vhInputLabel);

// Leaflet Map Initialization
var map = L.map('map').setView([37.7749, -122.4194], 10); // San Francisco Coordinates

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Initialize date pickers
flatpickr("#start_date", {dateFormat: "Y-m-d"});
flatpickr("#end_date", {dateFormat: "Y-m-d"});

// Get values from user inputs
document.getElementById('start_date').addEventListener('change', function() {
  const startDate = this.value;
  console.log("Start Date:", startDate);
});

document.getElementById('end_date').addEventListener('change', function() {
  const endDate = this.value;
  console.log("End Date:", endDate);
});

document.getElementById('area_name').addEventListener('input', function() {
  const areaName = this.value;
  console.log("Area Name:", areaName);
});

document.getElementById('distance').addEventListener('input', function() {
  const distance = this.value;
  console.log("Distance:", distance);
});

document.querySelectorAll('input[name="raster_band"]').forEach(function(radio) {
  radio.addEventListener('change', function() {
    const rasterBand = this.value;
    console.log("Raster Band:", rasterBand);
  });
});
*/