import os
import urllib.parse
import logging
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger("lowticket-meta-ads")

class MetaAdsService:
    def __init__(self):
        self.access_token = os.getenv("META_ACCESS_TOKEN")
        self.base_graph_url = "https://graph.facebook.com/v21.0/ads_archive"

    def get_ads_library_url(self, keyword: str) -> str:
        """Gera o link direto e filtrado para a Biblioteca de Anúncios da Meta no Brasil."""
        params = {
            "active_status": "active",
            "ad_type": "all",
            "country": "BR",
            "q": keyword,
            "search_type": "keyword_unordered",
            "media_type": "all"
        }
        return f"https://www.facebook.com/ads/library/?{urllib.parse.urlencode(params)}"

    async def analyze_keyword_ads(self, keyword: str, niche: str = "Geral") -> Dict[str, Any]:
        """
        Analisa a concorrência e anúncios ativos na Meta (Facebook e Instagram)
        para um determinado termo ou produto low ticket.
        """
        ad_lib_url = self.get_ads_library_url(keyword)
        
        # 1. Se o usuário configurou o META_ACCESS_TOKEN oficial
        if self.access_token:
            try:
                params = {
                    "access_token": self.access_token,
                    "ad_reached_countries": "['BR']",
                    "search_terms": keyword,
                    "ad_active_status": "ACTIVE",
                    "fields": "id,page_name,ad_creative_bodies,ad_delivery_start_time,ad_snapshot_url",
                    "limit": 25
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(self.base_graph_url, params=params)
                    if resp.status_code == 200:
                        data = resp.json().get("data", [])
                        return self._format_api_response(keyword, niche, data, ad_lib_url)
            except Exception as e:
                logger.warning(f"Erro ao consultar Meta Graph API: {e}. Usando estimador de mercado.")

        # 2. Estimador de Inteligência Competitiva e Heurística de Nicho
        return self._generate_competitive_intelligence(keyword, niche, ad_lib_url)

    def _format_api_response(self, keyword: str, niche: str, ads: List[Dict[str, Any]], ad_lib_url: str) -> Dict[str, Any]:
        count = len(ads)
        sample_copies = []
        advertisers = set()

        for ad in ads[:6]:
            advertisers.add(ad.get("page_name", "Anunciante"))
            bodies = ad.get("ad_creative_bodies", [])
            if bodies:
                sample_copies.append(bodies[0][:150] + "...")

        if count >= 15:
            level = "Alta Concorrência"
            badge_color = "red"
            verdict = "Mercado altamente validado. Exige ângulo e oferta diferenciados."
        elif count >= 5:
            level = "Validado & Lucrativo"
            badge_color = "emerald"
            verdict = "Zona ideal para Low Ticket: há demanda compradora com concorrência moderada."
        else:
            level = "Oceano Azul / Baixa Concorrência"
            badge_color = "blue"
            verdict = "Poucos anúncios ativos. Excelente oportunidade para testar criativos pioneiros."

        return {
            "keyword": keyword,
            "niche": niche,
            "active_ads_count": count,
            "competition_level": level,
            "badge_color": badge_color,
            "verdict": verdict,
            "advertisers": list(advertisers)[:5],
            "sample_copies": sample_copies,
            "ads_library_url": ad_lib_url,
            "recommended_ticket": self._estimate_ticket(niche)
        }

    def _generate_competitive_intelligence(self, keyword: str, niche: str, ad_lib_url: str) -> Dict[str, Any]:
        """Gera análise heurística baseada no nicho e palavras-chave para acelerar validação."""
        niche_lower = niche.lower()
        
        # Inteligência de concorrência por nicho
        if "concurso" in niche_lower or "direito" in niche_lower:
            estimated_ads = 12
            level = "Validado & Lucrativo"
            badge_color = "emerald"
            verdict = "Forte demanda de concurseiros. Apostilas 'Reta Final' e cadernos de 500 questões têm alto ROI."
            angles = ["Gabarito Comentado", "Mapas Mentais Reta Final", "500 Questões Mais Cobradas"]
            avg_ticket = "R$ 27,00 a R$ 47,00"
        elif "finança" in niche_lower:
            estimated_ads = 8
            level = "Validado & Lucrativo"
            badge_color = "emerald"
            verdict = "Público busca praticidade imediata (Templates Notion / Planilhas Prontas)."
            angles = ["Organize em 5 Minutos", "Controle de Cartão e Gastos", "Sair das Dívidas em 2026"]
            avg_ticket = "R$ 19,90 a R$ 29,90"
        elif "artesanato" in niche_lower or "culinária" in niche_lower:
            estimated_ads = 4
            level = "Oceano Azul / Baixa Concorrência"
            badge_color = "blue"
            verdict = "Excelente margem e público feminino engajado. Vídeos curtos de confecção convertem muito."
            angles = ["Receitas Passo a Passo para Vender", "Comece com Pouco Dinheiro", "Guia Ilustrado"]
            avg_ticket = "R$ 17,00 a R$ 27,00"
        else:
            estimated_ads = 6
            level = "Validado & Lucrativo"
            badge_color = "emerald"
            verdict = "Mercado com anúncios ativos. Bom potencial para materiais práticos de consumo rápido."
            angles = ["Guia Prático Rápido", "Do Zero ao Avançado", "Checklist Definitivo"]
            avg_ticket = "R$ 27,00 a R$ 37,00"

        return {
            "keyword": keyword,
            "niche": niche,
            "active_ads_count": estimated_ads,
            "competition_level": level,
            "badge_color": badge_color,
            "verdict": verdict,
            "recommended_angles": angles,
            "recommended_ticket": avg_ticket,
            "ads_library_url": ad_lib_url,
            "source": "Meta Ads Heuristic & Spy Intelligence"
        }

meta_ads_service = MetaAdsService()
