import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Clustering from './pages/Clustering';
import Overview from './pages/Overview';
import Preprocessing from './pages/Preprocessing';

function AppLayout() {
  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'sans-serif' }}>
      
      <Sidebar />

      <div style={{ flexGrow: 1, backgroundColor: '#F8FAFC', padding: '32px', overflowY: 'auto' }}>
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/preprocessing" element={<Preprocessing />} />
          <Route path="/clustering" element={<Clustering />} />
        </Routes>
      </div>
      
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}