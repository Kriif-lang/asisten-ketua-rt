import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class LangflowEngine:
    """
    Engine utama yang menggunakan Langflow sebagai orkestrator pipeline.
    Flow: ChatInput → Language Model (Google Gemini) → ChatOutput
    """

    def __init__(self):
        self.api_url  = os.getenv("LANGFLOW_API_URL", "").rstrip("/")
        self.flow_id  = os.getenv("LANGFLOW_FLOW_ID", "")
        self.api_key  = os.getenv("LANGFLOW_API_KEY", "")
        self.timeout  = int(os.getenv("LANGFLOW_TIMEOUT", "30"))
        self.is_connected = False

        if self.api_url and self.flow_id:
            self._test_connection()

    def _get_token(self) -> str:
        """Ambil JWT token dari Langflow local via auto_login."""
        try:
            resp = requests.get(f"{self.api_url}/api/v1/auto_login", timeout=5)
            if resp.status_code == 200:
                return resp.json().get("access_token", "")
        except Exception:
            pass
        return ""

    def _test_connection(self):
        """Cek konektivitas ke Langflow instance dan pastikan edge CI->LM ada."""
        try:
            if not self.api_key:
                self._token = self._get_token()
            resp = requests.get(
                f"{self.api_url}/api/v1/flows/{self.flow_id}",
                headers=self._headers(),
                timeout=5
            )
            self.is_connected = resp.status_code == 200
            if self.is_connected:
                self._ensure_ci_lm_edge(resp.json())
        except Exception:
            self.is_connected = False

    def _ensure_ci_lm_edge(self, flow: dict):
        """Pastikan edge ChatInput → LanguageModel ada di flow."""
        try:
            Q = "œ"
            ci_id = "ChatInput-vPKEw"
            lm_id = "LanguageModelComponent-GoogleAI"
            edges = flow.get("data", {}).get("edges", [])
            has_edge = any(e["source"] == ci_id and e["target"] == lm_id for e in edges)
            if has_edge:
                return

            def make_h(d):
                parts = []
                for k, v in d.items():
                    if isinstance(v, list):
                        vals = ",".join(f"{Q}{x}{Q}" for x in v)
                        parts.append(f"{Q}{k}{Q}:[{vals}]")
                    else:
                        parts.append(f"{Q}{k}{Q}:{Q}{v}{Q}")
                return "{" + ",".join(parts) + "}"

            ci_src = make_h({"dataType": "ChatInput", "id": ci_id, "name": "message", "output_types": ["Message"]})
            lm_tgt = make_h({"fieldName": "input_value", "id": lm_id, "inputTypes": ["Message"], "type": "other"})
            new_edge = {
                "id": f"reactflow__edge-{ci_id}{ci_src}-{lm_id}{lm_tgt}",
                "source": ci_id, "target": lm_id,
                "sourceHandle": ci_src, "targetHandle": lm_tgt,
                "animated": False,
                "data": {
                    "sourceHandle": {"dataType": "ChatInput", "id": ci_id, "name": "message", "output_types": ["Message"]},
                    "targetHandle": {"fieldName": "input_value", "id": lm_id, "inputTypes": ["Message"], "type": "other"}
                },
                "className": "", "selected": False
            }
            edges.append(new_edge)
            flow["data"]["edges"] = edges
            headers = {**self._headers(), "Content-Type": "application/json"}
            requests.patch(f"{self.api_url}/api/v1/flows/{self.flow_id}", headers=headers, json=flow, timeout=5)
        except Exception:
            pass

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        elif hasattr(self, "_token") and self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def consult(self, query: str) -> Dict[str, Any]:
        """Jalankan pertanyaan melalui Langflow flow."""
        if not self.is_connected:
            return {
                "answer": "Langflow tidak tersedia. Pastikan server Langflow berjalan di localhost:7860.",
                "sources": [],
                "engine": "offline"
            }
        return self._run_langflow(query)

    def _run_langflow(self, query: str) -> Dict[str, Any]:
        """Panggil Langflow API endpoint dan parse hasilnya."""
        try:
            payload = {
                "input_value": query,
                "input_type":  "chat",
                "output_type": "chat",
            }

            resp = requests.post(
                f"{self.api_url}/api/v1/run/{self.flow_id}",
                headers=self._headers(),
                json=payload,
                timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()

            # Parse response Langflow v1 - text dapat ada di message.text atau message.data.text
            msg = (
                data.get("outputs", [{}])[0]
                    .get("outputs", [{}])[0]
                    .get("results", {})
                    .get("message", {})
            )
            answer = msg.get("text", "") or msg.get("data", {}).get("text", "")

            if not answer:
                raise ValueError("Empty response from Langflow")

            return {
                "answer": answer,
                "sources": [],
                "engine": f"Langflow + Google Gemini (flow: {self.flow_id})"
            }

        except Exception as e:
            print(f"⚠️ Langflow error: {e}")
            self.is_connected = False
            return {
                "answer": f"Maaf, terjadi kesalahan: {e}",
                "sources": [],
                "engine": "error"
            }
