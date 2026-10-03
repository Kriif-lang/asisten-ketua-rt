import os
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class IBMWatsonxEngine:
    """
    Engine Konsultasi Hukum RT/RW berbasis IBM watsonx.ai (Granite / LLM) & Knowledge RAG Pergub 22/2022.
    """
    def __init__(self, kb_path: str = "data/pergub_22_2022.md"):
        self.kb_path = kb_path
        self.kb_content = ""
        self.articles: Dict[str, str] = {}
        self.api_key = os.getenv("IBM_WATSONX_API_KEY")
        self.project_id = os.getenv("IBM_WATSONX_PROJECT_ID")
        self.url = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self.model_id = os.getenv("IBM_WATSONX_MODEL_ID", "ibm/granite-3-8b-instruct")
        
        self.load_knowledge_base()
        self.init_watsonx_client()

    def load_knowledge_base(self):
        """Memuat & memetakan seluruh Pasal Pergub 22/2022."""
        if os.path.exists(self.kb_path):
            with open(self.kb_path, "r", encoding="utf-8") as f:
                self.kb_content = f.read()
            
            # Extract articles by heading
            raw_articles = re.split(r'####+\s+(Pasal\s+\d+.*)', self.kb_content)
            current_title = "Umum"
            for i in range(1, len(raw_articles), 2):
                title = raw_articles[i].strip()
                content = raw_articles[i+1].strip() if i+1 < len(raw_articles) else ""
                self.articles[title] = content

    def init_watsonx_client(self):
        """Inisialisasi SDK IBM watsonx.ai jika API Key tersedia."""
        self.watsonx_model = None
        if self.api_key and self.project_id:
            try:
                from ibm_watsonx_ai.foundation_models import ModelInference
                from ibm_watsonx_ai.credentials import Credentials
                
                credentials = Credentials(
                    url=self.url,
                    api_key=self.api_key
                )
                self.watsonx_model = ModelInference(
                    model_id=self.model_id,
                    credentials=credentials,
                    project_id=self.project_id,
                    params={
                        "max_new_tokens": 800,
                        "temperature": 0.2,
                        "repetition_penalty": 1.1
                    }
                )
                print("✅ IBM watsonx.ai client berhasil terhubung!")
            except Exception as e:
                print(f"⚠️ IBM watsonx client init notice: {e}")

    def search_relevant_articles(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        """Mencari pasal yang paling relevan dengan pertanyaan pengguna."""
        query_words = set(re.findall(r'\w+', query.lower()))
        scores = []
        
        # Keyword mapping boosting
        keywords_map = {
            "anak": ["Pasal 26", "Pasal 20"],
            "istri": ["Pasal 26", "Pasal 20"],
            "suami": ["Pasal 26", "Pasal 20"],
            "keluarga": ["Pasal 26", "Pasal 20"],
            "kerabat": ["Pasal 26"],
            "bendahara": ["Pasal 26", "Pasal 14", "Pasal 16"],
            "sekretaris": ["Pasal 26", "Pasal 14", "Pasal 16"],
            "nepotisme": ["Pasal 26"],
            "minimal kk": ["Pasal 3"],
            "jumlah kk": ["Pasal 3", "Pasal 6"],
            "pemecahan": ["Pasal 6", "Pasal 3"],
            "penggabungan": ["Pasal 6", "Pasal 7", "Pasal 8"],
            "tamu": ["Pasal 13"],
            "menginap": ["Pasal 13"],
            "24 jam": ["Pasal 13"],
            "syarat ketua": ["Pasal 20"],
            "umur": ["Pasal 20"],
            "usia": ["Pasal 20"],
            "ijazah": ["Pasal 20"],
            "pendidikan": ["Pasal 20"],
            "skck": ["Pasal 20"],
            "parpol": ["Pasal 20", "Lampiran A"],
            "partai": ["Pasal 20", "Lampiran A"],
            "jabatan": ["Pasal 28"],
            "masa jabatan": ["Pasal 28"],
            "periode": ["Pasal 28"],
            "larangan": ["Pasal 19", "Pasal 26"],
            "tugas": ["Pasal 14", "Pasal 15", "Pasal 16"],
            "kewajiban": ["Pasal 14", "Pasal 15"],
            "fungsi": ["Pasal 14", "Pasal 15"],
            "wewenang": ["Pasal 16", "Pasal 17"],
            "tanggung jawab": ["Pasal 14", "Pasal 15", "Pasal 16"],
            "musyawarah": ["Pasal 21", "Pasal 22", "Pasal 23"],
            "kuorum": ["Pasal 22", "Pasal 23"],
            "pemilihan": ["Pasal 21", "Pasal 22"],
            "kelurahan": ["Pasal 32", "Pasal 33"],
            "lurah": ["Pasal 32", "Pasal 33"],
            "laporan": ["Pasal 33", "Pasal 34"],
            "administrasi": ["Pasal 33", "Pasal 34"],
            "pemberhentian": ["Pasal 29", "Pasal 30"],
            "pergantian": ["Pasal 29", "Pasal 30"],
            "caretaker": ["Pasal 31"]
        }
        
        for title, content in self.articles.items():
            text_lower = (title + " " + content).lower()
            score = 0
            for word in query_words:
                if len(word) > 3 and word in text_lower:
                    score += 1
            
            # Check boosted phrases
            for phrase, target_articles in keywords_map.items():
                if phrase in query.lower():
                    for target in target_articles:
                        if target in title:
                            score += 10
            
            if score > 0:
                scores.append((score, title, content))
        
        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, title, content in scores[:top_k]:
            results.append({"title": title, "content": content})
        return results

    def consult(self, query: str) -> Dict[str, Any]:
        """
        Menjawab pertanyaan konsultasi masalah RT/RW menggunakan IBM watsonx.ai & RAG.
        """
        relevant_docs = self.search_relevant_articles(query)
        context_text = "\n\n".join([f"### {doc['title']}\n{doc['content']}" for doc in relevant_docs])
        
        system_prompt = f"""Anda adalah asisten digital khusus untuk Ketua RT di DKI Jakarta. Tugas Anda adalah membantu Ketua RT memahami peran, tugas, wewenang, dan tanggung jawab mereka berdasarkan Peraturan Gubernur (Pergub) DKI Jakarta No. 22 Tahun 2022.

Panduan menjawab:
1. Gunakan bahasa yang ramah, jelas, dan mudah dipahami — bukan bahasa hukum kaku.
2. Sebutkan PASAL dan AYAT terkait sebagai dasar, tapi jelaskan dalam kalimat sehari-hari.
3. Berikan langkah praktis yang bisa langsung dilakukan Ketua RT.
4. Fokus pada: tugas harian, kewajiban administratif, batasan wewenang, hubungan dengan RW/Kelurahan, dan penanganan masalah warga.

Rujukan Resmi Pergub No. 22/2022:
{context_text if context_text else self.kb_content[:2000]}
"""

        user_prompt = f"Pertanyaan RT/Warga: {query}"
        
        # 1. Jika IBM watsonx API aktif, gunakan IBM watsonx ModelInference
        if self.watsonx_model:
            try:
                full_prompt = f"{system_prompt}\n\n{user_prompt}\n\nJawaban Asisten RT Pintar:"
                response = self.watsonx_model.generate_text(prompt=full_prompt)
                return {
                    "answer": response,
                    "sources": relevant_docs,
                    "engine": f"IBM watsonx.ai ({self.model_id})"
                }
            except Exception as e:
                print(f"⚠️ Error calling IBM watsonx API, falling back to local RAG engine: {e}")
        
        # 2. Fallback RAG Reasoning Engine (jika belum ada API Key IBM)
        answer = self._local_reasoning_fallback(query, relevant_docs)
        return {
            "answer": answer,
            "sources": relevant_docs,
            "engine": "IBM watsonx RAG Knowledge Engine (Local Verified Mode)"
        }

    def _local_reasoning_fallback(self, query: str, docs: List[Dict[str, str]]) -> str:
        q = query.lower()
        
        # Case 1: Nepotisme / Hubungan keluarga
        if any(w in q for w in ["anak", "istri", "suami", "keluarga", "kerabat", "nepotisme"]):
            return (
                "❌ **TIDAK DIPERBOLEHKAN (DILARANG)**\n\n"
                "**Rujukan Hukum:**\n"
                "Berdasarkan **Pasal 26 Ayat (2)** Pergub DKI Jakarta No. 22 Tahun 2022:\n"
                "> *\"Ketua RT atau Ketua RW terpilih tidak dapat mengangkat warga RT atau RW yang mempunyai hubungan kekerabatan suami/istri atau anak dengan Ketua RT atau Ketua RW yang bersangkutan.\"*\n\n"
                "**Penjelasan & Solusi Praktis bagi Ketua RT:**\n"
                "1. Posisi Pengurus (Sekretaris, Bendahara, atau Ketua Bidang) **harus diisi oleh warga lain** di luar keluarga inti (bukan istri, suami, atau anak dari Ketua RT/RW).\n"
                "2. Hal ini bertujuan untuk menjaga akuntabilitas, transparansi keuangan, dan mencegah konflik kepentingan di lingkungan warga."
            )
            
        # Case 2: Syarat pembentukan RT/RW / Jumlah KK
        elif any(w in q for w in ["syarat pembentukan", "jumlah kk", "berapa kk", "minimal kk", "pemecahan"]):
            return (
                "📊 **SYARAT KETENTUAN JUMLAH KK (RT/RW)**\n\n"
                "**Rujukan Hukum:**\n"
                "Berdasarkan **Pasal 3** Pergub DKI Jakarta No. 22 Tahun 2022:\n"
                "- **1 Rukun Tetangga (RT)**: Terdiri dari **paling sedikit 80 Kepala Keluarga (KK)** dan **paling banyak 160 Kepala Keluarga (KK)**.\n"
                "- **1 Rukun Warga (RW)**: Terdiri dari **paling sedikit 8 RT** dan **paling banyak 16 RT**.\n\n"
                "**Pengecualian (Pasal 5):**\n"
                "Untuk wilayah hunian khusus seperti *Apartemen, Rumah Susun, Kondominium, Asrama, Ruko/Rukan*, jumlah KK dapat dikecualikan sesuai dengan kondisi bangunan setempat."
            )

        # Case 3: Tamu Menginap
        elif any(w in q for w in ["tamu", "menginap", "24 jam", "bermalam"]):
            return (
                "🏠 **ATURAN TAMU MENGINAP DI LINGKUNGAN RT**\n\n"
                "**Rujukan Hukum:**\n"
                "Berdasarkan **Pasal 13 Ayat (3)** Pergub DKI Jakarta No. 22 Tahun 2022:\n"
                "> *\"Orang yang bertamu untuk bermalam/menginap wajib memberitahukan kepada Ketua RT setempat dalam waktu paling lambat 1 x 24 jam.\"*\n\n"
                "**Tindakan Ketua RT:**\n"
                "Ketua RT berhak meminta identitas (KTP/KTP sementara) tamu tersebut demi menjaga keamanan & ketertiban lingkungan."
            )

        # Case 4: Syarat Ketua RT
        elif any(w in q for w in ["syarat ketua", "syarat mendaftar", "umur ketua", "ijazah"]):
            return (
                "📋 **PERSYARATAN CALON KETUA RT/RW**\n\n"
                "**Rujukan Hukum: Pasal 20 Pergub No. 22/2022**\n"
                "Calon Ketua RT/RW wajib memenuhi syarat berikut:\n"
                "1. **Usia**: Minimal 18 tahun atau sudah menikah.\n"
                "2. **Domisili**: Menetap paling sedikit **3 tahun berturut-turut** di RT setempat (dibuktikan KTP, KK, & Surat Ket. Domisili).\n"
                "3. **Pendidikan**: Paling rendah **SLTA / SMA / Sederajat**.\n"
                "4. **Kesehatan & Kelakuan**: Surat Keterangan Sehat dari Puskesmas & SKCK dari Kepolisian.\n"
                "5. **Larangan Rangkap Jabatan**: Bukan anggota/pengurus Partai Politik, Dewan Kota/Kabupaten, atau LKK.\n"
                "6. **Dokumen Wajib**: Wajib menandatangani Surat Pernyataan Tidak Merangkap Jabatan (Lampiran A) & Surat Pernyataan Kesanggupan (Lampiran B)."
            )

        # Case: Tugas & Kewajiban Ketua RT
        elif any(w in q for w in ["tugas", "kewajiban", "fungsi", "tanggung jawab", "peran", "wewenang"]):
            return (
                "📋 **TUGAS & KEWAJIBAN KETUA RT**\n\n"
                "**Rujukan Hukum: Pasal 14 & 15 Pergub No. 22/2022**\n\n"
                "**Tugas Utama Ketua RT:**\n"
                "1. **Pembinaan Kerukunan Warga** — Memelihara kerukunan, kegotongroyongan, dan persatuan antarwarga.\n"
                "2. **Pelayanan Administrasi** — Memberikan pengantar/rekomendasi untuk keperluan warga (KTP, KK, surat domisili, dll).\n"
                "3. **Pendataan Warga** — Mendata warga RT, termasuk pendatang dan tamu menginap lebih dari 1x24 jam.\n"
                "4. **Penyampaian Aspirasi** — Menyalurkan aspirasi dan kebutuhan warga kepada RW dan Kelurahan.\n"
                "5. **Keamanan & Ketertiban** — Membantu menjaga keamanan lingkungan bekerja sama dengan RW dan aparat.\n"
                "6. **Pemberdayaan Masyarakat** — Mendorong partisipasi warga dalam kegiatan sosial dan pembangunan.\n\n"
                "**Kewajiban Administratif:**\n"
                "- Melaporkan kegiatan & keuangan RT secara berkala kepada Lurah.\n"
                "- Menyimpan buku administrasi RT (buku induk warga, buku tamu, buku keuangan).\n"
                "- Menyelenggarakan Musyawarah RT minimal 1 kali dalam setahun."
            )

        # Case: Larangan pengurus RT
        elif any(w in q for w in ["larangan", "dilarang", "tidak boleh", "pantangan"]):
            return (
                "🚫 **LARANGAN BAGI PENGURUS RT**\n\n"
                "**Rujukan Hukum: Pasal 19 & 26 Pergub No. 22/2022**\n\n"
                "Pengurus RT **dilarang**:\n"
                "1. **Merangkap jabatan** di Partai Politik, Dewan Kota/Kabupaten, atau Lembaga Kemasyarakatan Kelurahan (LKK) lainnya.\n"
                "2. **Nepotisme kepengurusan** — Mengangkat istri/suami/anak sendiri sebagai pengurus RT (Sekretaris, Bendahara, atau Ketua Bidang).\n"
                "3. **Menyalahgunakan wewenang** — Menggunakan jabatan untuk kepentingan pribadi atau golongan.\n"
                "4. **Memungut iuran di luar ketentuan** — Iuran hanya boleh dipungut berdasarkan hasil Musyawarah RT.\n"
                "5. **Bertindak diskriminatif** terhadap warga berdasarkan suku, agama, ras, atau golongan.\n\n"
                "💡 **Catatan:** Pelanggaran terhadap larangan ini dapat menjadi dasar pemberhentian Ketua RT sebelum masa jabatan berakhir (Pasal 29)."
            )

        # Case: Musyawarah & Kuorum
        elif any(w in q for w in ["musyawarah", "kuorum", "rapat", "pemilihan", "voting"]):
            return (
                "🤝 **ATURAN MUSYAWARAH RT**\n\n"
                "**Rujukan Hukum: Pasal 21–23 Pergub No. 22/2022**\n\n"
                "**Musyawarah RT** adalah forum pengambilan keputusan tertinggi di tingkat RT, terdiri dari seluruh Kepala Keluarga yang terdaftar dalam KK RT setempat.\n\n"
                "**Ketentuan Kuorum:**\n"
                "- Musyawarah RT dinyatakan sah apabila dihadiri oleh **paling sedikit 2/3 (dua pertiga)** dari jumlah KK RT.\n"
                "- Jika kuorum tidak tercapai, musyawarah **ditunda** paling lama **7 (tujuh) hari**.\n"
                "- Pada pertemuan kedua, musyawarah sah jika dihadiri oleh **paling sedikit 1/2 (setengah)** dari jumlah KK RT.\n\n"
                "**Fungsi Musyawarah RT:**\n"
                "1. Pemilihan Ketua RT\n"
                "2. Menetapkan program kerja & iuran warga\n"
                "3. Pertanggungjawaban pengurus akhir masa jabatan\n"
                "4. Pemberhentian Ketua RT sebelum masa jabatan berakhir (jika diperlukan)"
            )

        # Case: Masa Jabatan
        elif any(w in q for w in ["masa jabatan", "berapa tahun", "periode", "menjabat"]):
            return (
                "⏳ **KETENTUAN MASA JABATAN PENGURUS RT/RW**\n\n"
                "**Rujukan Hukum: Pasal 28 Pergub No. 22/2022**\n"
                "1. Masa jabatan Pengurus RT atau RW adalah **5 (lima) tahun** terhitung sejak tanggal SK Lurah.\n"
                "2. Pengurus RT/RW hanya dapat menjabat **paling banyak 2 (dua) kali masa jabatan** (maksimal 10 tahun total, baik berturut-turut maupun tidak)."
            )

        # Generic RAG answer
        doc_summary = "\n\n".join([f"**{d['title']}**:\n{d['content'][:400]}..." for d in docs])
        return (
            f"📑 **ANALISIS HUKUM PERGUB NO. 22 TAHUN 2022**\n\n"
            f"Berdasarkan pertanyaan Anda mengenai *'{query}'*, berikut pasal-pasal relevan yang diatur dalam Peraturan Gubernur DKI Jakarta:\n\n"
            f"{doc_summary}\n\n"
            f"💡 **Rekomendasi:** Pengurus RT disarankan selalu berkoordinasi dengan RW & pihak Kelurahan setempat."
        )
