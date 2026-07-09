import { useEffect, useState } from 'react';
import DataTable from '../components/DataTable';

function StatCard({ title, subtitle, bgColor, iconColor, svgPath }) {
    return (
        <div style={{
            display: 'flex', alignItems: 'center', backgroundColor: '#ffffff',
            padding: '1rem', borderRadius: '0.5rem', border: '1px solid #E2E8F0',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)', height: '95px', flex: 1
        }}>
            <div style={{
                marginRight: '15px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                backgroundColor: bgColor, color: iconColor, padding: '10px', borderRadius: '8px'
            }}>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
                    <path d={svgPath} />
                </svg>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '13px', fontWeight: '600', color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{title}</span>
                <span style={{ fontSize: '16px', fontWeight: '700', color: '#0F172A', marginTop: '2px' }} dangerouslySetInnerHTML={{ __html: subtitle }}></span>
            </div>
        </div>
    );
}

export default function Overview() {
    const [stats, setStats] = useState({ total_comments: 0, total_posts: 0 });
    const [rawComments, setRawComments] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const selectedMonth = "2025-10";

    //   const dummyRawData = [
    //     { waktu: "2023-12-01 10:23", idPost: "CwXyZ1_abc", komentar: "air di daerah rungkut mati sudah 3 hari, tolong segera diperbaiki min" },
    //     { waktu: "2023-12-02 14:10", idPost: "CwXyZ2_def", komentar: "tagihan bulan ini kok naik banyak banget?? padahal jarang di rumah" },
    //     { waktu: "2023-12-03 08:05", idPost: "CwXyZ3_ghi", komentar: "Terimakasih PDAM sdh cepet respon keluhannya 🙏" },
    //     { waktu: "2023-12-04 19:30", idPost: "CwXyZ4_jkl", komentar: "min kapan airnya nyala lagi? dari pagi mati total" },
    //     { waktu: "2023-12-05 11:15", idPost: "CwXyZ5_mno", komentar: "pelayanan semakin membaik, tingkatkan terus pdam surya sembada" }
    //   ];

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                const resStats = await fetch(`http://localhost:8000/api/overview/${selectedMonth}`);
                if (!resStats.ok) throw new Error("Gagal mengambil data statistik");
                const dataStats = await resStats.json();

                const resRaw = await fetch(`http://localhost:8000/api/raw_comments/${selectedMonth}`);
                if (!resRaw.ok) throw new Error("Gagal mengambil data komentar mentah");
                const dataRaw = await resRaw.json();

                setStats(dataStats);
                setRawComments(dataRaw);
            } catch (err) {
                setError(err.message);
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, [selectedMonth]);

    if (isLoading) return <div style={{ padding: '20px' }}>Memuat data dari database...</div>;
    if (error) return <div style={{ padding: '20px', color: 'red' }}>Error: {error}</div>;

    const rawTableColumns = [
        { key: 'comment_date', label: 'Waktu Pembuatan' },
        { key: 'post_id', label: 'ID Post' },
        { key: 'raw_text', label: 'Komentar' }
    ];

    return (
        <div style={{ maxWidth: '1000px', margin: '0 auto', textAlign: 'left' }}>
            <h1 style={{ color: '#0F172A', marginBottom: '16px', lineHeight: '1' }}>Opinion Mining pada Komentar Instagram PDAM Surya Sembada</h1>
            <p style={{ color: '#475569', lineHeight: '1.6' }}>
                Dashboard ini menyajikan hasil <em>clustering</em> dan peringkasan otomatis yang diterapkan pada komentar publik di akun Instagram resmi PDAM Surya Sembada. Tujuannya adalah untuk memunculkan opini pelanggan yang berulang tanpa harus membaca setiap komentar secara manual.
            </p>

            <hr style={{ border: '0', borderTop: '1px solid #E2E8F0', margin: '32px 0' }} />

            <h2 style={{ fontSize: '20px', color: '#0F172A', marginBottom: '20px' }}>Dataset Overview</h2>
            <div style={{ display: 'flex', gap: '20px' }}>
                {/* <StatCard
                    title="Total Dataset"
                    subtitle="27000 Komentar"
                    bgColor="#dcfce7"
                    iconColor="#166534"
                    svgPath="M21 6.375c0 2.692-4.03 4.875-9 4.875S3 9.067 3 6.375 7.03 1.5 12 1.5s9 2.183 9 4.875Z M12 12.75c2.685 0 5.19-.586 7.078-1.609a8.283 8.283 0 0 0 1.897-1.384c.016.121.025.244.025.368C21 12.817 16.97 15 12 15s-9-2.183-9-4.875c0-.124.009-.247.025-.368a8.285 8.285 0 0 0 1.897 1.384C6.809 12.164 9.315 12.75 12 12.75Z"
                /> */}
                <StatCard
                    title="Total Dataset"
                    subtitle={`${stats.total_comments.toLocaleString('id-ID')} Komentar`}
                    bgColor="#dcfce7"
                    iconColor="#166534"
                    svgPath={"M21 6.375c0 2.692-4.03 4.875-9 4.875S3 9.067 3 6.375 7.03 1.5 12 1.5s9 2.183 9 4.875Z M12 12.75c2.685 0 5.19-.586 7.078-1.609a8.283 8.283 0 0 0 1.897-1.384c.016.121.025.244.025.368C21 12.817 16.97 15 12 15s-9-2.183-9-4.875c0-.124.009-.247.025-.368a8.285 8.285 0 0 0 1.897 1.384C6.809 12.164 9.315 12.75 12 12.75Z M12 16.5c2.685 0 5.19-.586 7.078-1.609a8.282 8.282 0 0 0 1.897-1.384c.016.121.025.244.025.368 0 2.692-4.03 4.875-9 4.875s-9-2.183-9-4.875c0-.124.009-.247.025-.368a8.284 8.284 0 0 0 1.897 1.384C6.809 15.914 9.315 16.5 12 16.5Z M12 20.25c2.685 0 5.19-.586 7.078-1.609a8.282 8.282 0 0 0 1.897-1.384c.016.121.025.244.025.368 0 2.692-4.03 4.875-9 4.875s-9-2.183-9-4.875c0-.124.009-.247.025-.368a8.284 8.284 0 0 0 1.897 1.384C6.809 19.664 9.315 20.25 12 20.25Z"}
                />
                <StatCard
                    title="Rentang Waktu Data"
                    subtitle="2023-01-01 - <br/>2023-12-31"
                    bgColor="#fee2e2"
                    iconColor="#991b1b"
                    svgPath="M12 11.993a.75.75 0 0 0-.75.75v.006c0 .414.336.75.75.75h.006a.75.75 0 0 0 .75-.75v-.006a.75.75 0 0 0-.75-.75H12ZM18 2.993a.75.75 0 0 0-1.5 0v1.5h-9V2.994a.75.75 0 1 0-1.5 0v1.497h-.752a3 3 0 0 0-3 3v11.252a3 3 0 0 0 3 3h13.5a3 3 0 0 0 3-3V7.492a3 3 0 0 0-3-3H18V2.993Z"
                />
                <StatCard
                    title="Bulan Terklaster"
                    subtitle="Desember 2023"
                    bgColor="#cbe6f3"
                    iconColor="#2e92c4"
                    svgPath="M1.5 7.125c0-1.036.84-1.875 1.875-1.875h6c1.036 0 1.875.84 1.875 1.875v3.75c0 1.036-.84 1.875-1.875 1.875h-6A1.875 1.875 0 0 1 1.5 10.875v-3.75Zm12 1.5c0-1.036.84-1.875 1.875-1.875h5.25c1.035 0 1.875.84 1.875 1.875v8.25c0 1.035-.84 1.875-1.875 1.875h-5.25a1.875 1.875 0 0 1-1.875-1.875v-8.25Z"
                />
            </div>

            <hr style={{ border: '0', borderTop: '1px solid #E2E8F0', margin: '32px 0' }} />

            <h2 style={{ fontSize: '20px', color: '#0F172A', marginBottom: '20px' }}>Pipeline Pengerjaan</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px' }}>
                <div>
                    <p style={{ fontWeight: '600', margin: '0 0 8px 0', fontSize: '14px' }}>1 · Pengumpulan</p>
                    <p style={{ fontSize: '13px', color: '#64748B', margin: 0 }}>Komentar Instagram diambil dari postingan resmi PDAM dengan cara web scraping.</p>
                </div>
                <div>
                    <p style={{ fontWeight: '600', margin: '0 0 8px 0', fontSize: '14px' }}>2 · Preprocessing</p>
                    <p style={{ fontSize: '13px', color: '#64748B', margin: 0 }}>Menormalkan bahasa gaul (slang), menghapus stopword, melakukan stemming token, dan menyamakan istilah sinonim.</p>
                </div>
                <div>
                    <p style={{ fontWeight: '600', margin: '0 0 8px 0', fontSize: '14px' }}>3 · Ekstraksi fitur</p>
                    <p style={{ fontSize: '13px', color: '#64748B', margin: 0 }}>Membangun vektor TF (4 skenario dengan pembobotan istilah yang berbeda).</p>
                </div>
                <div>
                    <p style={{ fontWeight: '600', margin: '0 0 8px 0', fontSize: '14px' }}>4 · Clustering</p>
                    <p style={{ fontSize: '13px', color: '#64748B', margin: 0 }}>Hierarchical Agglomerative Clustering dengan Valley-Tracing untuk menemukan nilai k yang optimal.</p>
                </div>
                <div>
                    <p style={{ fontWeight: '600', margin: '0 0 8px 0', fontSize: '14px' }}>5 · Summarisation</p>
                    <p style={{ fontSize: '13px', color: '#64748B', margin: 0 }}>(Tahapan belum dieksekusi) Menghasilkan kalimat ringkasan dan kata kunci teratas untuk setiap klaster.</p>
                </div>
            </div>

            <hr style={{ border: '0', borderTop: '1px solid #E2E8F0', margin: '32px 0' }} />

            <h2 style={{ fontSize: '20px', color: '#0F172A', marginBottom: '8px' }}>Data Mentah</h2>
            <p style={{ color: '#475569', fontSize: '14px', marginBottom: '20px' }}>
                Data komentar mentah yang tidak terstruktur yang diambil langsung dari Instagram sebelum proses pembersihan apa pun diterapkan.
            </p>

            <DataTable
                columns={rawTableColumns}
                data={rawComments}
                rowsPerPage={10}
            />

        </div>
    );
}