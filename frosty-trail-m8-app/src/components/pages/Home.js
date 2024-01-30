import React from 'react';
import '../../App.css';
import HeroSection from '../HeroSection';
import Footer from '../Footer';
import MapComponent from '../MapComponent';

function Home() {
  return (
    <>
      <HeroSection />
      <MapComponent />
      <Footer />
    </>
  );
}

export default Home;