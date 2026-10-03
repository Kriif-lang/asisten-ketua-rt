import os
import streamlit as st
from ibm_engine import IBMWatsonxEngine
from composio_helper import ComposioOrchestrator

st.set_page_config(
    page_title="Smart RT Assistant - Governance Platform",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Production Clean Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.4rem;
        color: #0F172A;
        font-weight: 800;
        margin-bottom: 0.1rem;
        letter-spacing: -0.5px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #475569;
        margin-bottom: 1.8rem;
    }
    .status-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 12px;
    }
    .badge-green {
        background-color: #10B981;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-blue {
        background-color: #2563EB;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def update_env_file(key_name: str, value: str):
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
            
    key_exists = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key_name}="):
            new_lines.append(f"{key_name}={value}\n")
            key_exists = True
        else:
            new_lines.append(line)
            
    if not key_exists:
        new_lines.append(f"{key_name}={value}\n")
        
    with open(env_path, "w") as f:
        f.writelines(new_lines)

# Initialize engines
@st.cache_resource
def get_engines():
    ibm_eng = IBMWatsonxEngine()
    comp_eng = ComposioOrchestrator()
    return ibm_eng, comp_eng

ibm_engine, composio_engine = get_engines()

# Header Production UI
st.markdown('<div class="main-header">🏠 Smart RT Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Platform Konsultasi Governance RT/RW & Pembuat Administrasi Otomatis | Berbasis <b>IBM watsonx.ai</b> & <b>Composio</b></div>', unsafe_allow_html=True)

# Sidebar Production Ready (Sangat Bersih)
st.sidebar.markdown("### 🏛️ **Pengurus RT/RW Digital**")
st.sidebar.caption("Sistem Tata Kelola Lingkungan DKI Jakarta")

st.sidebar.divider()
st.sidebar.markdown("#### **Status Sistem & Engine**")
st.sidebar.markdown("""
<div class="status-card">
    <b>IBM watsonx.ai</b> <span class="badge-blue">Active RAG</span><br>
    <small>Pergub No. 22/2022 Base</small>
</div>
<div class="status-card">
    <b>Composio Agent</b> <span class="badge-green">Connected 🟢</span><br>
    <small>Google Docs, Gmail, Sheets</small>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()

# Production API Key Manager (Collapsed so Sidebar Stays Extremely Clean)
with st.sidebar.expander("⚙️ **Pengaturan API & Kredensial (.env)**", expanded=False):
    st.caption("API Key tersimpan aman di file `.env` proyek.")
    
    current_composio_key = os.getenv("COMPOSIO_API_KEY", "")
    composio_input_key = st.text_input("Composio API Key:", type="password", value=current_composio_key)
    if st.button("💾 Simpan Key Composio"):
        if composio_input_key:
            composio_engine.init_composio(composio_input_key)
            os.environ["COMPOSIO_API_KEY"] = composio_input_key
            update_env_file("COMPOSIO_API_KEY", composio_input_key)
            st.success("API Key Composio tersimpan!")
            
    current_ibm_key = os.getenv("IBM_WATSONX_API_KEY", "")
    ibm_input_key = st.text_input("IBM watsonx API Key:", type="password", value=current_ibm_key)
    if st.button("💾 Simpan Key IBM"):
        if ibm_input_key:
            os.environ["IBM_WATSONX_API_KEY"] = ibm_input_key
            update_env_file("IBM_WATSONX_API_KEY", ibm_input_key)
            st.success("API Key IBM tersimpan!")

st.sidebar.caption("© 2026 Smart RT Assistant — Powered by IBM & Composio")

# Tabs utama
tab1, tab2, tab3 = st.tabs([
    "💬 Konsultasi Hukum RT/RW (IBM watsonx)", 
    "📄 Auto-Generate Surat Resmi (Composio PDF)", 
    "⚡ Dashboard Integrasi Tools (Composio)"
])

# TAB 1: Konsultasi Hukum RT/RW
with tab1:
    st.subheader("💡 Konsultasi Permasalahan Lingkungan RT/RW")
    st.write("Tanyakan permasalahan atau aturan seputar RT/RW di DKI Jakarta. AI akan menjawab berdasarkan rujukan resmi Pergub No. 22/2022.")

    st.markdown("**Pertanyaan Sering Diajukan (Klik untuk Coba):**")
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    
    selected_prompt = ""
    if col_q1.button("❓ Bolehkah anak Ketua RT jadi Bendahara?"):
        selected_prompt = "Bolehkah anak saya yang merupakan Ketua RT diangkat menjadi bendahara RT?"
    if col_q2.button("❓ Berapa minimal KK untuk membentuk RT?"):
        selected_prompt = "Berapa jumlah minimal KK untuk membentuk 1 RT di Jakarta?"
    if col_q3.button("❓ Aturan tamu menginap 1x24 jam"):
        selected_prompt = "Bagaimana aturan hukum mengenai tamu menginap lebih dari 24 jam?"
    if col_q4.button("❓ Berapa masa jabatan Ketua RT?"):
        selected_prompt = "Berapa lama masa jabatan Ketua RT dan berapa periode maksimalnya?"

    user_query = st.text_input("Ketik pertanyaan Anda di sini:", value=selected_prompt if selected_prompt else "", placeholder="Contoh: Apakah calon ketua RT boleh berasal dari pengurus partai politik?")
    
    if st.button("🔍 Tanya Asisten RT", type="primary") or user_query:
        if user_query:
            with st.spinner("IBM watsonx RAG Engine sedang menganalisis Pergub 22/2022..."):
                res = ibm_engine.consult(user_query)
                
                st.markdown(f"*(Engine: `{res['engine']}`)*")
                st.markdown(res['answer'])
                
                with st.expander("📚 Lihat Pasal & Rujukan Resmi Terkait"):
                    for src in res.get('sources', []):
                        st.markdown(f"**{src['title']}**")
                        st.caption(src['content'])

# TAB 2: Auto-Generate Surat Resmi
with tab2:
    st.subheader("📄 Generator Surat Administrasi RT/RW (Lampiran Pergub 22/2022)")
    st.write("Pilih jenis surat yang ingin dibuat. Sistem akan memformat PDF resmi sesuai standar Gubernur DKI Jakarta.")

    jenis_surat = st.selectbox("Pilih Format Surat Resmi:", [
        "Lampiran I: Surat Pengantar Warga (Buat KTP/KK/Nikah)",
        "Lampiran A: Surat Pernyataan Tidak Merangkap Jabatan (Parpol/LKK)",
        "Lampiran B: Surat Pernyataan Kesanggupan Melaksanakan Tugas",
        "Lampiran E: Berita Acara Pemilihan Ketua RT"
    ])

    st.divider()

    if "Lampiran I" in jenis_surat:
        st.markdown("### 📝 Form Surat Pengantar Warga (Lampiran I)")
        col_a, col_b = st.columns(2)
        with col_a:
            rt_no = st.text_input("Nomor RT", value="005")
            rw_no = st.text_input("Nomor RW", value="03")
            kelurahan = st.text_input("Kelurahan", value="Menteng")
            kecamatan = st.text_input("Kecamatan", value="Menteng")
            kota = st.text_input("Kota Administrasi", value="Jakarta Pusat")
            nama_warga = st.text_input("Nama Lengkap Warga", value="Ahmad Rifki")
            ttl = st.text_input("Tempat/Tgl Lahir Warga", value="Jakarta, 12 Agustus 1995")
            
        with col_b:
            nik = st.text_input("NIK / No. KTP Warga", value="3171011208950001")
            jk = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            agama = st.text_input("Agama", value="Islam")
            pekerjaan = st.text_input("Pekerjaan", value="Karyawan Swasta")
            alamat = st.text_area("Alamat Rumah", value="Jl. Kebon Sirih No. 45 RT 005/RW 03")
            keperluan = st.text_input("Keperluan / Maksud Surat", value="Permohonan Pembuatan KTP Baru & Kartu Keluarga")

        if st.button("🚀 Generate PDF Surat Pengantar", type="primary"):
            data_pdf = {
                "rt": rt_no, "rw": rw_no, "kelurahan": kelurahan, "kecamatan": kecamatan,
                "kota": kota, "nama": nama_warga, "ttl": ttl, "nik": nik,
                "jenis_kelamin": jk, "agama": agama, "pekerjaan": pekerjaan,
                "alamat": alamat, "keperluan": keperluan
            }
            output_file = "output_surat_pengantar.pdf"
            path = composio_engine.generate_surat_pengantar_pdf(data_pdf, output_file)
            
            st.success("✅ PDF Surat Pengantar Berhasil Dibuat!")
            with open(path, "rb") as f:
                st.download_button(
                    label="📥 Download Surat Pengantar (PDF)",
                    data=f,
                    file_name=f"Surat_Pengantar_RT{rt_no}_{nama_warga.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )

    elif "Lampiran A" in jenis_surat:
        st.markdown("### 📝 Form Surat Pernyataan Tidak Merangkap Jabatan (Lampiran A)")
        col_c, col_d = st.columns(2)
        with col_c:
            rt_no = st.text_input("Untuk Calon Ketua RT", value="005")
            rw_no = st.text_input("Untuk Calon Ketua RW", value="03")
            nama_calon = st.text_input("Nama Calon", value="Budi Santoso")
            ttl_calon = st.text_input("Tempat/Tgl Lahir", value="Jakarta, 05 Mei 1982")
        with col_d:
            nik_calon = st.text_input("Nomor NIK/KTP", value="3171010505820003")
            pekerjaan_calon = st.text_input("Pekerjaan", value="Wiraswasta")
            alamat_calon = st.text_area("Alamat Rumah", value="Jl. Menteng Raya No. 10")

        if st.button("🚀 Generate PDF Surat Pernyataan (Lampiran A)", type="primary"):
            data_a = {
                "rt": rt_no, "rw": rw_no, "nama": nama_calon, "ttl": ttl_calon,
                "nik": nik_calon, "pekerjaan": pekerjaan_calon, "alamat": alamat_calon
            }
            output_file_a = "output_lampiran_a.pdf"
            path_a = composio_engine.generate_surat_pernyataan_parpol_pdf(data_a, output_file_a)
            
            st.success("✅ PDF Surat Pernyataan Berhasil Dibuat!")
            with open(path_a, "rb") as f:
                st.download_button(
                    label="📥 Download Surat Pernyataan Lampiran A (PDF)",
                    data=f,
                    file_name=f"Lampiran_A_Pernyataan_{nama_calon.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )

    elif "Lampiran B" in jenis_surat:
        st.markdown("### 📝 Form Surat Pernyataan Kesanggupan (Lampiran B)")
        col_e, col_f = st.columns(2)
        with col_e:
            rt_no_b = st.text_input("Nomor RT", value="005", key="rt_b")
            rw_no_b = st.text_input("Nomor RW", value="03", key="rw_b")
            nama_b = st.text_input("Nama Lengkap Calon", value="Budi Santoso", key="nama_b")
            ttl_b = st.text_input("Tempat/Tgl Lahir", value="Jakarta, 05 Mei 1982", key="ttl_b")
        with col_f:
            nik_b = st.text_input("Nomor NIK/KTP", value="3171010505820003", key="nik_b")
            pekerjaan_b = st.text_input("Pekerjaan", value="Wiraswasta", key="pekerjaan_b")
            alamat_b = st.text_area("Alamat Rumah", value="Jl. Menteng Raya No. 10", key="alamat_b")

        if st.button("🚀 Generate PDF Surat Kesanggupan (Lampiran B)", type="primary"):
            data_b = {
                "rt": rt_no_b, "rw": rw_no_b, "nama": nama_b, "ttl": ttl_b,
                "nik": nik_b, "pekerjaan": pekerjaan_b, "alamat": alamat_b
            }
            output_file_b = "output_lampiran_b.pdf"
            path_b = composio_engine.generate_surat_kesanggupan_pdf(data_b, output_file_b)
            
            st.success("✅ PDF Surat Pernyataan Kesanggupan Berhasil Dibuat!")
            with open(path_b, "rb") as f:
                st.download_button(
                    label="📥 Download Surat Kesanggupan Lampiran B (PDF)",
                    data=f,
                    file_name=f"Lampiran_B_Kesanggupan_{nama_b.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )

    elif "Lampiran E" in jenis_surat:
        st.markdown("### 📝 Form Berita Acara Pemilihan Ketua RT (Lampiran E)")
        col_g, col_h = st.columns(2)
        with col_g:
            rt_e = st.text_input("Nomor RT", value="005", key="rt_e")
            rw_e = st.text_input("Nomor RW", value="03", key="rw_e")
            kelurahan_e = st.text_input("Kelurahan", value="Menteng", key="kel_e")
            tempat_e = st.text_input("Tempat Pemilihan", value="Balai Warga RT 005", key="tempat_e")
        with col_h:
            ketua_panitia = st.text_input("Nama Ketua Panitia", value="Drs. H. Mulyadi", key="pan_ketua")
            sekretaris_panitia = st.text_input("Nama Sekretaris Panitia", value="Siti Aminah, S.Pd", key="pan_sek")
            pemenang_e = st.text_input("Nama Ketua RT Terpilih", value="Sdr. Budi Santoso", key="pem_e")

        if st.button("🚀 Generate PDF Berita Acara Pemilihan (Lampiran E)", type="primary"):
            data_e = {
                "rt": rt_e, "rw": rw_e, "kelurahan": kelurahan_e, "tempat": tempat_e,
                "panitia_ketua": ketua_panitia, "panitia_sekretaris": sekretaris_panitia,
                "pemenang": pemenang_e
            }
            output_file_e = "output_lampiran_e.pdf"
            path_e = composio_engine.generate_berita_acara_pemilihan_pdf(data_e, output_file_e)
            
            st.success("✅ PDF Berita Acara Pemilihan Berhasil Dibuat!")
            with open(path_e, "rb") as f:
                st.download_button(
                    label="📥 Download Berita Acara Lampiran E (PDF)",
                    data=f,
                    file_name=f"Lampiran_E_BeritaAcara_RT{rt_e}.pdf",
                    mime="application/pdf"
                )

# TAB 3: Composio Tools Orchestration Manager
with tab3:
    st.subheader("⚡ Composio Integration & Automation Manager")
    st.write("Orkestra berbagai aplikasi (Google Workspace, Notion, Slack, Gmail) untuk otomatisasi alur kerja pengurus RT/RW.")

    st.markdown("### 🔍 Status Akun Terhubung (Connected Accounts):")
    if st.button("🔄 Verifikasi Ulang Koneksi Composio", type="primary"):
        with st.spinner("Mengkueri status akun terhubung dari API Composio..."):
            accs = composio_engine.verify_connected_accounts()
            st.success(f"Berhasil memverifikasi {len(accs)} akun terhubung!")
            for acc in accs:
                st.markdown(f"- 🟢 **App**: `{acc['app']}` | **Status**: `{acc['status']}` | **ID**: `{acc['id']}`")

    st.divider()
    st.markdown("### 🔌 Integrasi Tools Composio Terpasang:")
    actions = composio_engine.get_available_actions()
    for act in actions:
        with st.expander(f"🔹 {act['app']} — `{act['action']}`"):
            st.write(act['description'])
            if st.button(f"Uji Aksi {act['app']}", key=f"btn_{act['action']}"):
                res = composio_engine.execute_composio_action(act['action'], {"test": True, "app": act['app']})
                st.json(res)
