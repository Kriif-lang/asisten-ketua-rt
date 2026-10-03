# Asisten Ketua RT — DKI Jakarta

Aplikasi chat berbasis AI untuk membantu Ketua RT di DKI Jakarta memahami tugas, wewenang, dan kewajiban mereka berdasarkan **Peraturan Gubernur DKI Jakarta No. 22 Tahun 2022**.

---

## Deskripsi Project

Project ini dibuat untuk hackathon IBM x Composio. Aplikasi ini menjawab pertanyaan seputar kepengurusan RT secara akurat dengan menyertakan rujukan pasal sebagai dasar hukum, sehingga Ketua RT tidak perlu membaca dokumen Pergub yang panjang secara manual.

---

## Arsitektur Sistem

```
User (Browser)
     │
     ▼
Streamlit App (app.py)
     │
     ▼
LangflowEngine (langflow_engine.py)
     │  POST /api/v1/run/{flow_id}
     ▼
IBM Langflow (localhost:7860)
     │
     ├── Node: Chat Input
     ├── Node: Language Model — Google Gemini gemini-3.8-flash
     └── Node: Chat Output
               │
               ▼
         Google Gemini API
```

---

## Teknologi yang Digunakan

| Teknologi | Peran |
|-----------|-------|
| **IBM Langflow** | Orkestrator flow AI — mengelola pipeline input → LLM → output |
| **IBM Bob IDE** | Editor kode — mengisi credential API key di file `.env` |
| **Google Gemini (gemini-3.8-flash)** | Model bahasa untuk menjawab pertanyaan |
| **Streamlit** | Web interface aplikasi chat |
| **Composio** | Integrasi tools eksternal (API key tersimpan di `.env`) |

---

## IBM Langflow — Detail Flow

Flow yang dibuat di Langflow terdiri dari 3 node:

1. **Chat Input** — menerima pertanyaan user dari Streamlit
2. **Language Model** — memproses pertanyaan dengan Google Gemini. Node ini dikonfigurasi dengan *system message* yang menetapkan AI sebagai asisten berbasis Pergub No. 22/2022, temperature 0.1 untuk konsistensi jawaban hukum
3. **Chat Output** — mengembalikan respons ke aplikasi

Setiap pertanyaan user dikirim via `POST /api/v1/run/{flow_id}` ke Langflow, diproses oleh Gemini, dan hasilnya dikembalikan ke Streamlit.

---

## IBM Bob IDE

Bob digunakan untuk mengisi file `.env` dengan API key yang dibutuhkan sistem:
- `GOOGLE_AI_API_KEY` — untuk akses Google Gemini melalui Langflow
- `COMPOSIO_API_KEY` — untuk integrasi Composio

Credential yang diisi di Bob kemudian didaftarkan ke Langflow Global Variables, sehingga node Language Model bisa mengakses Google Gemini secara otomatis.

---

## Fitur Aplikasi

- Menjawab pertanyaan seputar tugas, wewenang, dan kewajiban Ketua RT
- Setiap jawaban menyertakan rujukan pasal Pergub sebagai dasar hukum
- Suggestion buttons untuk pertanyaan umum
- Tombol Chat Baru untuk memulai percakapan baru
- Tampilan dark mode yang bersih

---

## Cara Menjalankan

**Prasyarat:** IBM Langflow berjalan di `localhost:7860`

```bash
# Clone & masuk ke folder
cd ibm-composio-app

# Install dependencies
pip install -r requirements.txt

# Isi credential di .env
cp .env.example .env
# Edit .env dengan API key yang sesuai

# Jalankan aplikasi
streamlit run app.py
```

Buka browser di `http://localhost:8501`

---

## Struktur Folder

```
ibm-composio-app/
├── app.py                 # Streamlit web app
├── langflow_engine.py     # Integrasi dengan IBM Langflow API
├── composio_helper.py     # Integrasi Composio
├── ibm_engine.py          # Engine fallback lokal
├── data/
│   └── pergub_22_2022.md  # Knowledge base Pergub No. 22/2022
├── requirements.txt
└── .env                   # API keys (tidak di-commit)
```

---

## Screenshot

**Empty state — halaman awal**

Tampilan saat aplikasi baru dibuka, dengan suggestion buttons untuk pertanyaan umum.

**Contoh jawaban**

Setiap jawaban disertai rujukan pasal Pergub dan dapat diakses melalui tombol "Lihat rujukan pasal".
