import React from 'react';
import '../../App.css';
import HeroSection from '../HeroSection';
import MapWithDrawing from '../MapWithDrawing';
import Footer from '../Footer';

function Home() {
  return (
    <>
      <HeroSection />
      <MapWithDrawing />
      <Footer />
    </>
  );
}

export default Home;