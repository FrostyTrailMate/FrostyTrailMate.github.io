import { MapContainer, TileLayer} from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
//import RasterSAR from './geojsons/merged_image.tiff';
//import RasterSARaux from './geojsons/merged_image.tiff.aux.xml';

const Raster = () => {

  return (
    <div style={{ backgroundColor: '#242424', padding: '30px' }}>
      <MapContainer
        center={[37.8451, -119.5383]}
        zoom={10}
        style={{ height: '400px', width: '40%',margin: 'Right' }}>

        <TileLayer
          url="https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=749cd9dc6622478d9454b931ded7943d"
          subdomains={['mt0', 'mt1', 'mt2', 'mt3']}
          attribution='© Thunderforest by Gravitystorm Limited.'/>
          
      </MapContainer>
    </div>
  );
};

export default Raster;