import React from 'react';
import { Link } from 'react-router-dom';

function Footer() {
  const handleClick = () => {
    window.scrollTo(0, 0); // Scrolls to the top when the link is clicked
  };

  return (
    <div className='footer-container'>
      <div className='footer-links'>
        <div className='footer-link-wrapper'>
          <div className='footer-link-items'>
            <Link to='/about' onClick={handleClick}><h2>About Us</h2></Link>
          </div>
        </div>
        <div className='footer-link-wrapper'>
          <div className='footer-link-items'>
            <a href='https://www.youtube.com/watch?v=yBDHkveJUf4'><h2>Youtube <i className='fab fa-youtube'/></h2></a>
          </div>
          <div className='footer-link-items'>
            <a href='https://www.instagram.com/sbastiansuarezz/'><h2>Instagram <i className='fab fa-instagram'/> </h2></a>
          </div>
        </div>
      </div>
      <div className='footer-logo'>
        <Link to='/' className='social-logo' onClick={handleClick}> Frosty Trail M8 <i className='fas fa-snowflake' /></Link>
      </div>
      <div>
        <small className='website-rights'> FTM8 © 2024 </small>
      </div>
    </div>
  );
}

export default Footer;
