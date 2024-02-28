import React from 'react';
import '../CSStyles/About.css';
import video from './../images/video1.mp4';

function About() {
  return (
  <>
    <div className='textabout'>
      <span><strong>Welcome to Frosty Trail Mate</strong>, your essential companion for navigating hiking trails, anywhere
      in the world! Our project emerged from the desire to simplify the hiking experience by providing precise 
      information about the location of snow on the trails. Explore trails confidently with our user-friendly 
      platform, ensuring you stay informed about snow locations for a seamless and enjoyable hiking adventure!
      </span>
      </div>
      <video autoPlay muted loop id="video-background">
        <source src={video} type="video/mp4" />
      </video>
      <div className='textabout2'>
      <span ><strong>By:</strong> Christopher H, Sebastian S and Carolina</span>
      </div>
    </>
  );
}

export default About;
