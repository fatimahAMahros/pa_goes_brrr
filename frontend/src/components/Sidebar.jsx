import { Link, useLocation } from 'react-router-dom';

function NavLink({ to, children }) {
  const location = useLocation();
  const isActive = location.pathname === to;
  
  return (
    <Link 
      to={to} 
      style={{ 
        display: 'block', 
        padding: '10px 15px', 
        marginBottom: '8px',
        textDecoration: 'none', 
        color: isActive ? '#0F172A' : '#64748B',
        backgroundColor: isActive ? '#F1F5F9' : 'transparent',
        fontWeight: isActive ? '600' : '400',
        borderRadius: '6px'
      }}
    >
      {children}
    </Link>
  );
}

export default function Sidebar() {
  return (
    <div style={{ 
      width: '280px', 
      backgroundColor: '#ffffff', 
      borderRight: '1px solid #E2E8F0',
      padding: '24px',
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      boxSizing: 'border-box'
    }}>
      <div style={{ width: '100%', minHeight: '120px', backgroundColor: '#E2E8F0', borderRadius: '8px', marginBottom: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748B' }}>Logo Area</div>
      
      <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: '#0F172A' }}>
        Komentar Instagram Perumda Surya Sembada
      </h3>
      <hr style={{ border: '0', borderTop: '1px solid #E2E8F0', marginBottom: '16px', width: '100%' }} />
      
      <nav style={{ flexGrow: 1 }}>
        <NavLink to="/">Overview</NavLink>
        <NavLink to="/preprocessing">Preprocessing</NavLink>
        <NavLink to="/clustering">Clustering</NavLink>
      </nav>

      <hr style={{ border: '0', borderTop: '1px solid #E2E8F0', margin: '16px 0', width: '100%' }} />
      
      <span style={{ fontSize: '12px', color: '#94A3B8' }}>
        Final Project · Automatic Clustering
      </span>
    </div>
  );
}