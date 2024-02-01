import React from 'react';
import './Footer.css';
import { Link } from 'react-router-dom';

function Footer() {
  return (
    <div className='footer-container'>
      <div class='footer-links'>

        <div className='footer-link-wrapper'>
          <div class='footer-link-items'>
            <Link to='/About'><h2>About Us</h2></Link>
          </div>
        </div>
        <div className='footer-link-wrapper'>
          <div class='footer-link-items'>
            <Link to='https://www.youtube.com/watch?v=yBDHkveJUf4'><h2>Tutorial <i class='fab fa-youtube'/></h2></Link>
          </div>
          <div class='footer-link-items'>
            <Link to='https://www.instagram.com/sbastiansuarezz/'><h2>Instagram <i class='fab fa-instagram'/> </h2></Link>
          </div>
        </div>
      </div>
          <div class='footer-logo'>
            <Link to='/' className='social-logo'> Frosty Trail M8 <i class=' fas fa-snowflake' /></Link>
          </div>
          <div>
            <small class='website-rights'> FTM8 © 2024 </small>
          </div>
    </div>
  );
}

export default Footer;