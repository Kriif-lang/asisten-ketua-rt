import os
import streamlit as st
from composio_helper import ComposioOrchestrator

st.set_page_config(
    page_title="Asisten Ketua RT — DKI Jakarta",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        color: #0F172A;
        font-weight: 800;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    .sub-header {
        font-size: 1rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .new-chat-row {
        position: fixed;
        top: 12px;
        right: 18px;
        z-index: 999;
    }
    .engine-badge {
        font-size: 0.75rem;
        color: #6B7280;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)


def get_secret(key, default=""):
    try:
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


@st.cache_data
def load_pergub():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pergub_22_2022.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


@st.cache_resource
def get_gemini_client():
    api_key = get_secret("GOOGLE_AI_API_KEY")
    if not api_key:
        return None, None
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        pergub = load_pergub()
        system_prompt = f"""Kamu adalah Asisten AI untuk Ketua RT di DKI Jakarta.
Tugasmu menjawab pertanyaan seputar tugas, wewenang, dan administrasi RT/RW berdasarkan Peraturan Gubernur DKI Jakarta Nomor 22 Tahun 2022.

Aturan menjawab:
1. Jawab dalam Bahasa Indonesia yang sopan dan mudah dipahami oleh pengurus RT
2. Selalu sertakan rujukan pasal dari Pergub No. 22/2022 bila relevan (contoh: "Berdasarkan Pasal 3...")
3. Bila pertanyaan di luar cakupan Pergub 22/2022, sampaikan dengan sopan

Berikut isi lengkap Pergub No. 22/2022 sebagai referensi:

{pergub}
"""
        return client, system_prompt
    except Exception as e:
        st.error(f"Gagal menghubungkan ke Google Gemini: {e}")
        return None, None


@st.cache_resource
def get_composio():
    return ComposioOrchestrator()


gemini_client, system_prompt = get_gemini_client()
composio_engine = get_composio()

# Header
st.markdown('<div class="main-header">🏠 Asisten Ketua RT</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Konsultasi berbasis <b>Pergub DKI Jakarta No. 22/2022</b> • Ditenagai <b>IBM Langflow + Google Gemini</b></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🏛️ Asisten Ketua RT")
    st.caption("Platform Digital RT/RW DKI Jakarta")
    st.divider()
    st.markdown("#### Status Sistem")
    if gemini_client:
        st.success("Google Gemini: Terhubung ✅")
    else:
        st.error("Google Gemini: Tidak terhubung ❌")
        st.info("Set `GOOGLE_AI_API_KEY` di Streamlit Secrets")
    st.divider()
    st.caption("© 2026 Asisten Ketua RT — IBM Langflow + Google Gemini")

# Tabs
tab1, tab2 = st.tabs(["💬 Konsultasi RT/RW", "📄 Generator Surat PDF"])

# ─── TAB 1: KONSULTASI ───────────────────────────────────────────────────────
with tab1:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = None

    # Tombol Chat Baru
    if st.session_state.messages:
        st.markdown('<div class="new-chat-row">', unsafe_allow_html=True)
        if st.button("✏️ Chat Baru", key="new_chat"):
            st.session_state.messages = []
            st.session_state.chat_session = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Suggestion buttons
    if not st.session_state.messages:
        st.markdown("**Pertanyaan yang sering diajukan:**")
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        suggestions = {
            "q1": "Berapa minimal KK untuk membentuk RT di Jakarta?",
            "q2": "Berapa lama masa jabatan Ketua RT dan maksimal periodenya?",
            "q3": "Bolehkah anak Ketua RT menjadi Bendahara RT?",
            "q4": "Aturan tamu menginap lebih dari 1×24 jam bagaimana?",
        }
        selected = ""
        if col1.button("❓ Syarat pembentukan RT", key="q1"):
            selected = suggestions["q1"]
        if col2.button("❓ Masa jabatan Ketua RT", key="q2"):
            selected = suggestions["q2"]
        if col3.button("❓ Anak Ketua RT jadi Bendahara?", key="q3"):
            selected = suggestions["q3"]
        if col4.button("❓ Aturan tamu menginap", key="q4"):
            selected = suggestions["q4"]
        if selected:
            st.session_state.messages.append({"role": "user", "content": selected})
            st.rerun()

    # Tampilkan riwayat chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input chat
    if prompt := st.chat_input("Ketik pertanyaan Anda tentang RT/RW..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

    # Generate jawaban untuk pesan user terakhir yang belum dijawab
    if (st.session_state.messages
            and st.session_state.messages[-1]["role"] == "user"):
        user_text = st.session_state.messages[-1]["content"]
        with st.chat_message("assistant"):
            if not gemini_client:
                answer = "Maaf, Google Gemini tidak terhubung. Pastikan `GOOGLE_AI_API_KEY` sudah dikonfigurasi."
                st.markdown(answer)
            else:
                with st.spinner("Mencari referensi Pergub 22/2022..."):
                    try:
                        import time
                        from google.genai import types
                        model_name = get_secret("GOOGLE_AI_MODEL", "gemini-2.5-flash")
                        history = []
                        for msg in st.session_state.messages[:-1]:
                            role = "user" if msg["role"] == "user" else "model"
                            history.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
                        history.append(types.Content(role="user", parts=[types.Part(text=user_text)]))
                        cfg = types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.1)
                        answer = None
                        for attempt in range(3):
                            try:
                                response = gemini_client.models.generate_content(
                                    model=model_name, contents=history, config=cfg
                                )
                                answer = response.text
                                break
                            except Exception as e:
                                if "503" in str(e) and attempt < 2:
                                    time.sleep(3)
                                else:
                                    raise e
                        if not answer:
                            answer = "Maaf, server sedang sibuk. Coba lagi dalam beberapa detik."
                    except Exception as e:
                        answer = f"Maaf, terjadi kesalahan: {e}"
                    st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

# ─── TAB 2: GENERATOR SURAT ──────────────────────────────────────────────────
with tab2:
    st.subheader("📄 Generator Surat Administrasi RT/RW")
    st.write("Buat dokumen resmi sesuai lampiran Pergub No. 22/2022 dalam format PDF.")

    jenis_surat = st.selectbox("Pilih Format Surat:", [
        "Lampiran I: Surat Pengantar Warga",
        "Lampiran A: Surat Pernyataan Tidak Merangkap Jabatan",
        "Lampiran B: Surat Pernyataan Kesanggupan Melaksanakan Tugas",
        "Lampiran E: Berita Acara Pemilihan Ketua RT",
    ])

    st.divider()

    if "Lampiran I" in jenis_surat:
        st.markdown("### 📝 Surat Pengantar Warga (Lampiran I)")
        col_a, col_b = st.columns(2)
        with col_a:
            rt_no = st.text_input("Nomor RT", value="005")
            rw_no = st.text_input("Nomor RW", value="03")
            kelurahan = st.text_input("Kelurahan", value="Menteng")
            kecamatan = st.text_input("Kecamatan", value="Menteng")
            kota = st.text_input("Kota Administrasi", value="Jakarta Pusat")
            nama_warga = st.text_input("Nama Lengkap Warga", value="Ahmad Rifki")
            ttl = st.text_input("Tempat/Tgl Lahir", value="Jakarta, 12 Agustus 1995")
        with col_b:
            nik = st.text_input("NIK / No. KTP", value="3171011208950001")
            jk = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            agama = st.text_input("Agama", value="Islam")
            pekerjaan = st.text_input("Pekerjaan", value="Karyawan Swasta")
            alamat = st.text_area("Alamat Rumah", value="Jl. Kebon Sirih No. 45 RT 005/RW 03")
            keperluan = st.text_input("Keperluan Surat", value="Permohonan Pembuatan KTP Baru")
        if st.button("🚀 Generate PDF Surat Pengantar", type="primary"):
            data_pdf = {
                "rt": rt_no, "rw": rw_no, "kelurahan": kelurahan,
                "kecamatan": kecamatan, "kota": kota, "nama": nama_warga,
                "ttl": ttl, "nik": nik, "jenis_kelamin": jk,
                "agama": agama, "pekerjaan": pekerjaan,
                "alamat": alamat, "keperluan": keperluan
            }
            path = composio_engine.generate_surat_pengantar_pdf(data_pdf, "output_surat_pengantar.pdf")
            with open(path, "rb") as f:
                st.download_button("📥 Download PDF", data=f,
                    file_name=f"Surat_Pengantar_RT{rt_no}_{nama_warga.replace(' ', '_')}.pdf",
                    mime="application/pdf")

    elif "Lampiran A" in jenis_surat:
        st.markdown("### 📝 Surat Pernyataan Tidak Merangkap Jabatan (Lampiran A)")
        col_c, col_d = st.columns(2)
        with col_c:
            rt_no = st.text_input("Nomor RT", value="005")
            rw_no = st.text_input("Nomor RW", value="03")
            nama_calon = st.text_input("Nama Calon", value="Budi Santoso")
            ttl_calon = st.text_input("Tempat/Tgl Lahir", value="Jakarta, 05 Mei 1982")
        with col_d:
            nik_calon = st.text_input("Nomor NIK/KTP", value="3171010505820003")
            pekerjaan_calon = st.text_input("Pekerjaan", value="Wiraswasta")
            alamat_calon = st.text_area("Alamat Rumah", value="Jl. Menteng Raya No. 10")
        if st.button("🚀 Generate PDF (Lampiran A)", type="primary"):
            data_a = {
                "rt": rt_no, "rw": rw_no, "nama": nama_calon, "ttl": ttl_calon,
                "nik": nik_calon, "pekerjaan": pekerjaan_calon, "alamat": alamat_calon
            }
            path_a = composio_engine.generate_surat_pernyataan_parpol_pdf(data_a, "output_lampiran_a.pdf")
            with open(path_a, "rb") as f:
                st.download_button("📥 Download PDF", data=f,
                    file_name=f"Lampiran_A_{nama_calon.replace(' ', '_')}.pdf",
                    mime="application/pdf")

    elif "Lampiran B" in jenis_surat:
        st.markdown("### 📝 Surat Pernyataan Kesanggupan (Lampiran B)")
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
        if st.button("🚀 Generate PDF (Lampiran B)", type="primary"):
            data_b = {
                "rt": rt_no_b, "rw": rw_no_b, "nama": nama_b, "ttl": ttl_b,
                "nik": nik_b, "pekerjaan": pekerjaan_b, "alamat": alamat_b
            }
            path_b = composio_engine.generate_surat_kesanggupan_pdf(data_b, "output_lampiran_b.pdf")
            with open(path_b, "rb") as f:
                st.download_button("📥 Download PDF", data=f,
                    file_name=f"Lampiran_B_{nama_b.replace(' ', '_')}.pdf",
                    mime="application/pdf")

    elif "Lampiran E" in jenis_surat:
        st.markdown("### 📝 Berita Acara Pemilihan Ketua RT (Lampiran E)")
        col_g, col_h = st.columns(2)
        with col_g:
            rt_e = st.text_input("Nomor RT", value="005", key="rt_e")
            rw_e = st.text_input("Nomor RW", value="03", key="rw_e")
            kelurahan_e = st.text_input("Kelurahan", value="Menteng", key="kel_e")
            tempat_e = st.text_input("Tempat Pemilihan", value="Balai Warga RT 005", key="tempat_e")
        with col_h:
            ketua_panitia = st.text_input("Nama Ketua Panitia", value="Drs. H. Mulyadi")
            sekretaris_panitia = st.text_input("Nama Sekretaris Panitia", value="Siti Aminah, S.Pd")
            pemenang_e = st.text_input("Nama Ketua RT Terpilih", value="Sdr. Budi Santoso")
        if st.button("🚀 Generate PDF (Lampiran E)", type="primary"):
            data_e = {
                "rt": rt_e, "rw": rw_e, "kelurahan": kelurahan_e, "tempat": tempat_e,
                "panitia_ketua": ketua_panitia, "panitia_sekretaris": sekretaris_panitia,
                "pemenang": pemenang_e
            }
            path_e = composio_engine.generate_berita_acara_pemilihan_pdf(data_e, "output_lampiran_e.pdf")
            with open(path_e, "rb") as f:
                st.download_button("📥 Download PDF", data=f,
                    file_name=f"Lampiran_E_RT{rt_e}.pdf",
                    mime="application/pdf")
