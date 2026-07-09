import { useState } from 'react';

export default function DataTable({ columns, data, rowsPerPage = 10 }) {
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.ceil(data.length / rowsPerPage) || 1;

  const startIndex = (currentPage - 1) * rowsPerPage;
  const currentData = data.slice(startIndex, startIndex + rowsPerPage);

  const handlePrev = () => setCurrentPage((prev) => Math.max(prev - 1, 1));
  const handleNext = () => setCurrentPage((prev) => Math.min(prev + 1, totalPages));

  return (
    <div style={{ border: '1px solid #E2E8F0', borderRadius: '8px', overflow: 'hidden', backgroundColor: '#fff' }}>
      
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px', textAlign: 'left' }}>
          
          <thead style={{ backgroundColor: '#F8FAFC' }}>
            <tr>
              {columns.map((col, index) => (
                <th key={index} style={{ padding: '12px 16px', color: '#475569', fontWeight: '600', whiteSpace: 'nowrap', borderBottom: '1px solid #E2E8F0' }}>
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          
          <tbody>
            {currentData.length > 0 ? (
              currentData.map((row, rowIndex) => (
                <tr key={rowIndex} style={{ backgroundColor: rowIndex % 2 === 0 ? '#ffffff' : '#F1F5F9' }}>
                  {columns.map((col, colIndex) => (
                    <td key={colIndex} style={{ padding: '12px 4px', borderBottom: '1px solid #E2E8F0', color: '#0F172A' }}>
                      {row[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} style={{ padding: '20px', textAlign: 'center', color: '#64748B' }}>
                  Tidak ada data.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', backgroundColor: '#F8FAFC', borderTop: '1px solid #E2E8F0' }}>
        <span style={{ fontSize: '13px', color: '#64748B' }}>
          Menampilkan {data.length > 0 ? startIndex + 1 : 0} - {Math.min(startIndex + rowsPerPage, data.length)} dari {data.length.toLocaleString('id-ID')} data
        </span>
        
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            onClick={handlePrev} 
            disabled={currentPage === 1}
            style={{ 
              padding: '6px 12px', border: '1px solid #CBD5E1', borderRadius: '6px', 
              backgroundColor: currentPage === 1 ? '#F1F5F9' : '#fff', 
              cursor: currentPage === 1 ? 'not-allowed' : 'pointer', 
              fontSize: '13px', color: currentPage === 1 ? '#94A3B8' : '#0F172A' 
            }}
          >
            Sebelumnya
          </button>
          
          <span style={{ fontSize: '13px', color: '#0F172A', padding: '6px 12px' }}>
            Hal {currentPage} / {totalPages}
          </span>
          
          <button 
            onClick={handleNext} 
            disabled={currentPage === totalPages}
            style={{ 
              padding: '6px 12px', border: '1px solid #CBD5E1', borderRadius: '6px', 
              backgroundColor: currentPage === totalPages ? '#F1F5F9' : '#fff', 
              cursor: currentPage === totalPages ? 'not-allowed' : 'pointer', 
              fontSize: '13px', color: currentPage === totalPages ? '#94A3B8' : '#0F172A' 
            }}
          >
            Selanjutnya
          </button>
        </div>
      </div>
      
    </div>
  );
}