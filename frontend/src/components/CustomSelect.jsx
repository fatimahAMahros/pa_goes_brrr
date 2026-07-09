
export default function CustomSelect({ label, value, onChange, options, containerStyle }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', ...containerStyle }}>
      
      {label && (
        <label style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#0F172A' }}>
          {label}
        </label>
      )}
      
      <select 
        value={value} 
        onChange={onChange}
        style={{ 
          padding: '10px', 
          borderRadius: '6px', 
          border: '1px solid #CBD5E1', 
          backgroundColor: '#fff', 
          color: '#0F172A',
          width: '100%',
          outline: 'none',
          cursor: 'pointer'
        }}
      >
        {options.map((opt, index) => (
          <option key={index} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      
    </div>
  );
}