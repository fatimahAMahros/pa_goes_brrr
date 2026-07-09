import { useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  Tooltip as RechartsTooltip,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  XAxis, YAxis
} from 'recharts';
import CustomSelect from '../components/CustomSelect';

export default function Clustering() {
  const [selectedMonth, setSelectedMonth] = useState('2023-12');
  const monthOptions = [
    { value: '2023-12', label: 'Desember 2023' }
  ];

  const scenarioOptions = [
    { value: '1', label: '1' },
    { value: '2', label: '2' },
    { value: '3', label: '3' },
    { value: '4', label: '4' }
  ];

  const linkageOptions = [
    { value: 'complete', label: 'Complete' },
    { value: 'average', label: 'Average' },
    { value: 'single', label: 'Single' },
    { value: 'centroid', label: 'Centroid' }
  ];

  const [selectedScenario, setSelectedScenario] = useState('4');
  const [selectedLinkage, setSelectedLinkage] = useState('centroid');

  const optimalK = 58;
  const dummyValleyData = Array.from({ length: 80 }, (_, i) => ({
    k: i + 2,
    metric: Math.max(10, 100 - (i * 3) + Math.random() * 5 + (i > 56 ? (i - 56) * 1.5 : 0))
  }));

  const dummyDistData = [
    { name: "C1 - Keluhan Air Mati", count: 8500 },
    { name: "C2 - Tagihan Membengkak", count: 4200 },
    { name: "C3 - Pipa Bocor", count: 3100 },
    { name: "C4 - Layanan Pelanggan", count: 1200 },
    { name: "Misc - Gabungan Minoritas (54 Klaster)", count: 10000 },
  ];

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', textAlign: 'left', paddingBottom: '50px' }}>
      
      <h1 style={{ color: '#0F172A', marginBottom: '16px', lineHeight: '1' }}>Metode & Hasil Klastering</h1>
      <p style={{ color: '#475569', lineHeight: '1.6' }}>
        Halaman ini menggabungkan pencarian nilai k optimal menggunakan <strong>Valley-Tracing</strong> dengan eksplorasi hasil topik pembicaraan pelanggan (Opinion Mining). Pilih bulan dan konfigurasi klastering di bawah ini.
      </p>

      <hr style={{ border: '0', borderTop: '1px solid #E2E8F0', margin: '32px 0' }} />

      {/* SELECTORS
      <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <label style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#0F172A' }}>Bulan</label>
          <select 
            value={selectedMonth} 
            onChange={(e) => setSelectedMonth(e.target.value)}
            style={{ padding: '10px', borderRadius: '6px', border: '1px solid #CBD5E1', backgroundColor: '#fff' }}
          >
            <option value="2023-12">Desember 2023</option>
          </select>
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <label style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#0F172A' }}>Skenario</label>
          <select 
            value={selectedScenario} 
            onChange={(e) => setSelectedScenario(e.target.value)}
            style={{ padding: '10px', borderRadius: '6px', border: '1px solid #CBD5E1', backgroundColor: '#fff' }}
          >
            <option value="1">1</option>
            <option value="2">2</option>
            <option value="3">3</option>
            <option value="4">4</option>
          </select>
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <label style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#0F172A' }}>Metode Linkage</label>
          <select 
            value={selectedLinkage} 
            onChange={(e) => setSelectedLinkage(e.target.value)}
            style={{ padding: '10px', borderRadius: '6px', border: '1px solid #CBD5E1', backgroundColor: '#fff' }}
          >
            <option value="complete">Complete</option>
            <option value="average">Average</option>
            <option value="single">Single</option>
            <option value="centroid">Centroid</option>
          </select>
        </div>
      </div> */}
      <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
        
        <CustomSelect 
          label="Bulan"
          value={selectedMonth}
          onChange={(e) => setSelectedMonth(e.target.value)}
          options={monthOptions}
          containerStyle={{ flex: 1 }}
        />

        <CustomSelect 
          label="Skenario"
          value={selectedScenario}
          onChange={(e) => setSelectedScenario(e.target.value)}
          options={scenarioOptions}
          containerStyle={{ flex: 1 }}
        />

        <CustomSelect 
          label="Metode Linkage"
          value={selectedLinkage}
          onChange={(e) => setSelectedLinkage(e.target.value)}
          options={linkageOptions}
          containerStyle={{ flex: 1 }}
        />
        
      </div>

      <div style={{ 
        backgroundColor: '#dcfce7', border: '1px solid #16a34a', borderLeft: '4px solid #16a34a', 
        borderRadius: '0.5rem', padding: '0.85rem 1.1rem', display: 'flex', gap: '10px', marginBottom: '32px' 
      }}>
        <div style={{ marginTop: '2px' }}>
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="#16a34a" width="18" height="18">
            <path strokeLinecap="round" strokeLinejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
          </svg>
        </div>
        <div style={{ fontSize: '13.5px', color: '#0F172A', lineHeight: '1.55' }}>
          <span style={{ fontWeight: '600' }}>Kombinasi yang Direkomendasikan: Complete Linkage – Skenario 4.</span> Hasil kombinasi ini cenderung paling mudah dibaca, meskipun tidak selalu optimal untuk setiap bulan.
        </div>
      </div>

      <hr style={{ border: '0', borderTop: '1px solid #E2E8F0', margin: '32px 0' }} />

      <h2 style={{ fontSize: '18px', color: '#0F172A', marginBottom: '8px' }}>Kurva Valley-Tracing: Penentuan k Optimal</h2>
      <p style={{ fontSize: '13px', color: '#64748B', marginBottom: '20px' }}>
        Lembah pada <strong>k = {optimalK}</strong> terpilih sebagai jumlah klaster optimal — ini adalah titik di mana metrik berhenti membaik secara signifikan saat jumlah klaster ditambah.
      </p>

      <div style={{ width: '100%', height: '340px', backgroundColor: '#fff', border: '1px solid #E2E8F0', borderRadius: '8px', padding: '20px 20px 20px 0' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={dummyValleyData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
            <XAxis dataKey="k" tick={{ fontSize: 12 }} stroke="#94A3B8" />
            <YAxis tick={{ fontSize: 12 }} stroke="#94A3B8" />
            <RechartsTooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }} />
            
            <ReferenceLine x={optimalK} stroke="#D85A30" strokeDasharray="3 3" label={{ position: 'top', value: `k = ${optimalK}`, fill: '#D85A30', fontSize: 12, fontWeight: 'bold' }} />
            <ReferenceDot x={optimalK} y={dummyValleyData.find(d => d.k === optimalK)?.metric} r={6} fill="#D85A30" stroke="white" />
            
<Line type="linear" dataKey="metric" stroke="#185FA5" strokeWidth={2} dot={false} activeDot={{ r: 6 }} />          </LineChart>
        </ResponsiveContainer>
      </div>

      <hr style={{ border: '0', borderTop: '1px solid #E2E8F0', margin: '32px 0' }} />

      <h2 style={{ fontSize: '18px', color: '#0F172A', marginBottom: '20px' }}>Distribusi & Ringkasan Klaster</h2>
      
      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
        <div style={{ flex: 1, padding: '16px', border: '1px solid #E2E8F0', borderRadius: '8px', backgroundColor: '#fff' }}>
          <div style={{ fontSize: '13px', color: '#64748B' }}>Jumlah Klaster (k)</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#0F172A' }}>{optimalK}</div>
        </div>
        <div style={{ flex: 1, padding: '16px', border: '1px solid #E2E8F0', borderRadius: '8px', backgroundColor: '#fff' }}>
          <div style={{ fontSize: '13px', color: '#64748B' }}>Total Komentar</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#0F172A' }}>27,000</div>
        </div>
        <div style={{ flex: 1, padding: '16px', border: '1px solid #E2E8F0', borderRadius: '8px', backgroundColor: '#fff' }}>
          <div style={{ fontSize: '13px', color: '#64748B' }}>Klaster Terbesar</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#0F172A' }}>31%</div>
        </div>
      </div>

      <p style={{ fontWeight: '600', marginBottom: '16px', color: '#0F172A' }}>Distribusi Komentar per Klaster</p>
      <div style={{ width: '100%', height: '300px', marginBottom: '16px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart layout="vertical" data={dummyDistData} margin={{ top: 5, right: 30, left: 150, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E8F0" />
            <XAxis type="number" tick={{ fontSize: 12 }} stroke="#94A3B8" />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 12, fill: '#475569' }} width={140} />
            <RechartsTooltip cursor={{ fill: '#F1F5F9' }} contentStyle={{ borderRadius: '8px' }} />
            <Bar dataKey="count" fill="#185FA5" radius={[0, 4, 4, 0]} barSize={24} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p style={{ fontSize: '13px', color: '#64748B', fontStyle: 'italic', marginBottom: '32px' }}>
        *Terdapat 54 klaster minoritas yang digabungkan ke dalam satu grafik bar agar visualisasi distribusi komentar tetap rapi dan fokus pada topik utama.
      </p>

      <p style={{ fontWeight: '600', marginBottom: '16px', color: '#0F172A' }}>Detail Ringkasan Klaster</p>
      
      {dummyDistData.map((cluster, idx) => (
        <details key={idx} style={{ 
          marginBottom: '8px', border: '1px solid #E2E8F0', borderRadius: '8px', backgroundColor: '#fff', overflow: 'hidden' 
        }}>
          <summary style={{ 
            padding: '16px', fontWeight: '600', cursor: 'pointer', backgroundColor: '#F8FAFC', color: '#0F172A', listStyle: 'none', display: 'flex', justifyContent: 'space-between'
          }}>
            <span>{cluster.name}</span>
            <span style={{ color: '#64748B', fontWeight: '400' }}>{cluster.count.toLocaleString()} komentar</span>
          </summary>
          <div style={{ padding: '16px', borderTop: '1px solid #E2E8F0' }}>
            <p style={{ marginBottom: '12px', fontSize: '14px', color: '#475569' }}>
              <strong>Ringkasan:</strong> (Tahapan summarization belum dieksekusi)
            </p>
            <div style={{ marginBottom: '16px' }}>
              <strong style={{ fontSize: '14px', color: '#0F172A', display: 'block', marginBottom: '8px' }}>Kata kunci utama:</strong>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {['air', 'mati', 'lama', 'wilayah'].map(kw => (
                  <span key={kw} style={{ background: '#E6F1FB', color: '#185FA5', padding: '4px 12px', borderRadius: '12px', fontSize: '13px' }}>
                    {kw}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <strong style={{ fontSize: '14px', color: '#0F172A', display: 'block', marginBottom: '8px' }}>Contoh komentar:</strong>
              <blockquote style={{ borderLeft: '3px solid #CBD5E1', paddingLeft: '12px', margin: '0 0 8px 0', color: '#475569', fontSize: '14px' }}>
                "Air mati sudah 3 hari di wilayah rungkut, mohon tindakannya."
              </blockquote>
            </div>
          </div>
        </details>
      ))}

    </div>
  );
}