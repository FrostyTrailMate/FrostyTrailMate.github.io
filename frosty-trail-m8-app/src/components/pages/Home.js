import React from 'react';
import '../../App.css';
import HeroSection from '../HeroSection';
import MapComponent from '../MapComponent';
import Footer from '../Footer';

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