import os
import re
import urllib.parse
import logging
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger("lowticket-meta-ads")

class MetaAdsService:
    def __init__(self):
        self.access_token = os.getenv("META_ACCESS_TOKEN")
        self.base_graph_url = "https://graph.facebook.com/v21.0/ads_archive"

    def clean_search_term(self, raw_term: str) -> str:
        """
        Higieniza e extrai o núcleo da oferta para a Biblioteca de Anúncios da Meta.
        Remove prefixos de infoprodutos (Apostila/Guia Prático:), pontuação, anos no final
        e caracteres que quebram o motor de busca da Meta Ads Library.
        """
        if not raw_term:
            return ""
        
        term = raw_term.strip()

        # Se já for uma URL direta da Meta Ads ou de anúncio, preserva
        if term.startswith("http://") or term.startswith("https://"):
            return term

        # 1. Remover prefixos clássicos com pontuação (dois pontos, barras, etc.)
        prefixes_patterns = [
            r'^(?:apostila\s*[\/\-&e]\s*guia\s*pr[aá]tico\s*:\s*)',
            r'^(?:apostila\s*[\/\-&e]\s*guia\s*:\s*)',
            r'^(?:guia\s*pr[aá]tico\s*:\s*)',
            r'^(?:apostila\s*pr[aá]tica\s*:\s*)',
            r'^(?:apostila\s*completa\s*:\s*)',
            r'^(?:apostila\s*:\s*)',
            r'^(?:guia\s*:\s*)',
            r'^(?:e-?book\s*:\s*)',
            r'^(?:curso\s*:\s*)',
            r'^(?:manual\s*:\s*)',
            r'^(?:caderno\s*de\s*quest[oõ]es\s*:\s*)',
            r'^(?:caderno\s*:\s*)',
            r'^(?:super\s*pack\s*:\s*)',
            r'^(?:pack\s*:\s*)',
            r'^(?:kit\s*:\s*)',
            r'^(?:combo\s*:\s*)',
            r'^(?:protocolo\s*:\s*)',
            r'^(?:m[eé]todo\s*:\s*)',
            r'^(?:planilha\s*:\s*)',
            r'^(?:template\s*:\s*)'
        ]
        for pattern in prefixes_patterns:
            term = re.sub(pattern, '', term, flags=re.IGNORECASE).strip()

        # 2. Remover prefixos comuns sem dois pontos se sobrarem
        term = re.sub(r'^apostila\s+(?=concurso\b)', '', term, flags=re.IGNORECASE).strip()
        term = re.sub(r'^(?:guia\s*pr[aá]tico|caderno\s*de\s*quest[oõ]es|protocolo)\s+', '', term, flags=re.IGNORECASE).strip()

        # 3. Remover caracteres especiais que causam erro no analisador da Meta
        # / : ; | ! ? ~ * + " ' [ ] { } ( ) @ # $ % ^ & _ =
        term = re.sub(r'[\/:\;\|!\?~\*\+\"\'\[\]\{\}\(\)@#\$%\^&_=]', ' ', term)

        # 4. Remover hífens soltos
        term = re.sub(r'(?<=\s)-(?=\s)|^-\s*|\s*-$', ' ', term)

        # 5. Remover ano isolado no final (ex: '2026', '2025') caso haja outras palavras
        words = term.split()
        if len(words) > 2 and re.match(r'^202[4-9]$', words[-1]):
            words.pop()
            term = " ".join(words)

        # 6. Normalizar espaços múltiplos
        term = re.sub(r'\s+', ' ', term).strip()

        return term

    def get_broad_search_term(self, clean_term: str, niche: str = "Geral") -> str:
        """Gera um termo de busca mais amplo caso o usuário queira mapear todo o nicho."""
        words = clean_term.split()
        if len(words) >= 3:
            # Retorna as duas primeiras palavras principais
            return " ".join(words[:2])
        if len(words) <= 1 and niche and niche != "Geral":
            return f"{clean_term} {niche}".strip()
        return clean_term

    def get_ads_library_url(self, keyword: str, active_status: str = "all") -> str:
        """
        Gera o link direto e filtrado para a Biblioteca de Anúncios da Meta no Brasil.
        Usa 'active_status=all' por padrão para assegurar que anúncios recentes
        não sejam omitidos se pausados temporariamente pelos concorrentes.
        """
        # Se for uma URL direta de anúncio salva pelo usuário, retorna ela própria
        if keyword.startswith("http://") or keyword.startswith("https://"):
            return keyword

        clean_term = self.clean_search_term(keyword)
        if not clean_term:
            clean_term = keyword.strip()

        params = {
            "active_status": active_status,
            "ad_type": "all",
            "country": "BR",
            "q": clean_term,
            "search_type": "keyword_unordered",
            "media_type": "all"
        }
        return f"https://www.facebook.com/ads/library/?{urllib.parse.urlencode(params)}"

    def _estimate_ticket(self, niche: str) -> str:
        niche_lower = (niche or "").lower()
        if "concurso" in niche_lower or "direito" in niche_lower:
            return "R$ 27,00 a R$ 47,00"
        elif "finança" in niche_lower:
            return "R$ 19,90 a R$ 29,90"
        elif "artesanato" in niche_lower or "culinária" in niche_lower:
            return "R$ 17,00 a R$ 27,00"
        return "R$ 27,00 a R$ 37,00"

    async def analyze_keyword_ads(self, keyword: str, niche: str = "Geral") -> Dict[str, Any]:
        """
        Analisa a concorrência e anúncios ativos na Meta (Facebook e Instagram)
        para um determinado termo ou produto low ticket.
        """
        clean_term = self.clean_search_term(keyword)
        broad_term = self.get_broad_search_term(clean_term, niche)

        ad_lib_url = self.get_ads_library_url(clean_term, active_status="all")
        ad_lib_active_url = self.get_ads_library_url(clean_term, active_status="active")
        broad_ad_lib_url = self.get_ads_library_url(broad_term, active_status="all")
        
        # 1. Se o usuário configurou o META_ACCESS_TOKEN oficial
        if self.access_token:
            try:
                params = {
                    "access_token": self.access_token,
                    "ad_reached_countries": "['BR']",
                    "search_terms": clean_term,
                    "ad_active_status": "ALL",
                    "fields": "id,page_name,ad_creative_bodies,ad_delivery_start_time,ad_snapshot_url",
                    "limit": 25
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(self.base_graph_url, params=params)
                    if resp.status_code == 200:
                        data = resp.json().get("data", [])
                        return self._format_api_response(
                            keyword, clean_term, broad_term, niche, data,
                            ad_lib_url, ad_lib_active_url, broad_ad_lib_url
                        )
            except Exception as e:
                logger.warning(f"Erro ao consultar Meta Graph API: {e}. Usando estimador de mercado.")

        # 2. Estimador de Inteligência Competitiva e Heurística de Nicho
        return self._generate_competitive_intelligence(
            keyword, clean_term, broad_term, niche,
            ad_lib_url, ad_lib_active_url, broad_ad_lib_url
        )

    def _format_api_response(
        self, keyword: str, clean_term: str, broad_term: str, niche: str,
        ads: List[Dict[str, Any]], ad_lib_url: str, ad_lib_active_url: str, broad_ad_lib_url: str
    ) -> Dict[str, Any]:
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
            "clean_keyword": clean_term,
            "broad_keyword": broad_term,
            "niche": niche,
            "active_ads_count": count,
            "competition_level": level,
            "badge_color": badge_color,
            "verdict": verdict,
            "advertisers": list(advertisers)[:5],
            "sample_copies": sample_copies,
            "ads_library_url": ad_lib_url,
            "ads_library_active_url": ad_lib_active_url,
            "broad_ads_library_url": broad_ad_lib_url,
            "recommended_ticket": self._estimate_ticket(niche)
        }

    def _generate_competitive_intelligence(
        self, keyword: str, clean_term: str, broad_term: str, niche: str,
        ad_lib_url: str, ad_lib_active_url: str, broad_ad_lib_url: str
    ) -> Dict[str, Any]:
        """Gera análise heurística baseada no nicho e palavras-chave para acelerar validação."""
        niche_lower = (niche or "").lower()
        clean_lower = clean_term.lower()
        
        # Inteligência de concorrência por nicho
        if "concurso" in niche_lower or "direito" in niche_lower or "concurso" in clean_lower:
            estimated_ads = 12
            level = "Validado & Lucrativo"
            badge_color = "emerald"
            verdict = "Forte demanda de concurseiros. Apostilas 'Reta Final' e cadernos de 500 questões têm alto ROI."
            angles = ["Gabarito Comentado", "Mapas Mentais Reta Final", "500 Questões Mais Cobradas"]
            avg_ticket = "R$ 27,00 a R$ 47,00"
        elif "finança" in niche_lower or "notion" in clean_lower or "planner" in clean_lower:
            estimated_ads = 8
            level = "Validado & Lucrativo"
            badge_color = "emerald"
            verdict = "Público busca praticidade imediata (Templates Notion / Planilhas Prontas)."
            angles = ["Organize em 5 Minutos", "Controle de Cartão e Gastos", "Sair das Dívidas em 2026"]
            avg_ticket = "R$ 19,90 a R$ 29,90"
        elif "artesanato" in niche_lower or "culinária" in niche_lower or "amigurumi" in clean_lower:
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
            "clean_keyword": clean_term,
            "broad_keyword": broad_term,
            "niche": niche,
            "active_ads_count": estimated_ads,
            "competition_level": level,
            "badge_color": badge_color,
            "verdict": verdict,
            "recommended_angles": angles,
            "recommended_ticket": avg_ticket,
            "ads_library_url": ad_lib_url,
            "ads_library_active_url": ad_lib_active_url,
            "broad_ads_library_url": broad_ad_lib_url,
            "source": "Meta Ads Heuristic & Spy Intelligence"
        }

meta_ads_service = MetaAdsService()
