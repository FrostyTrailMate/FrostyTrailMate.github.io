import React, { useState} from 'react';
import { Link, useLocation } from 'react-router-dom';

function Navbar() {
  const [click, setClick] = useState(false);
  const location = useLocation();

  const handleClick = () => {
    setClick(!click);
    window.scrollTo(0, 0); // Scrolls to the top when a link is clicked
  };

  const handleLogoClick = () => {
    setClick(false); // Close mobile menu if logo is clicked
    window.scrollTo(0, 0); // Scrolls to the top when logo is clicked
    if (location.pathname === '/') {
      window.location.reload(); // Reload the page if already on the home page
    }
  };

  return (
    <>
      <nav className='navbar'>
        <div className='navbar-container'>
          <Link to='/' className='navbar-logo' onClick={handleLogoClick}> FTM8 <i className='fas fa-snowflake' /></Link>
          <div className='menu-icon' onClick={handleClick}>
            <i className={click ? 'fas fa-times' : 'fas fa-bars'} />
          </div>
          <ul className={click ? 'nav-menu active' : 'nav-menu'}>
          <li className='nav-item'>
              <Link to='/create' className='nav-links' onClick={handleClick}>
                Create
              </Link>
            </li>
            <li className='nav-item'>
              <Link to='/' className='nav-links' onClick={handleClick}>
                Results
              </Link>
            </li>
            <li className='nav-item'>
              <Link to='/about' className='nav-links' onClick={handleClick}>
                About us
              </Link>
            </li>
          </ul>
        </div>
      </nav>
    </>
  );
}

export default Navbar;


