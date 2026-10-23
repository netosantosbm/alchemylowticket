import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy.orm import Session
from models import AppSetting

logger = logging.getLogger("lowticket-ebook-generator")

def get_api_key(db: Optional[Session], key_name: str) -> Optional[str]:
    env_val = os.getenv(key_name.upper())
    if env_val:
        return env_val
    if db:
        setting = db.query(AppSetting).filter(AppSetting.key == key_name.lower()).first()
        if setting and setting.value:
            if isinstance(setting.value, dict):
                return setting.value.get("api_key") or setting.value.get("key")
            elif isinstance(setting.value, str):
                return setting.value.strip()
    return None

class EbookGeneratorService:
    """
    Serviço que gera Apostilas e E-books completos de Alto Valor Percebido,
    incluindo Slides de Orientação de Estudos, Fluxograma Visual e Capítulos Esquematizados.
    """

    async def generate_ebook(
        self,
        title: str,
        niche: str,
        target_audience: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        openai_key = get_api_key(db, "openai_api_key") or os.getenv("OPENAI_API_KEY")

        if openai_key:
            try:
                res = await self._generate_with_openai(openai_key, title, niche, target_audience)
                if res:
                    return res
            except Exception as e:
                logger.warning(f"Erro ao gerar com OpenAI: {e}. Usando motor nativo de estruturação didática.")

        return self._generate_native_visual_ebook(title, niche, target_audience)

    async def _generate_with_openai(
        self,
        api_key: str,
        title: str,
        niche: str,
        target_audience: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        clean_title = re.sub(r'^(Apostila/Guia Prático:\s*|Super Combo\s*|Guia\s*)', '', title, flags=re.IGNORECASE).strip()
        prompt = f"""
Você é um Especialista em Criação de Conteúdo Didático, Apostilas Esquematizadas e Materiais de Estudo para Infoprodutos Low Ticket de Alta Conversão.
Gere uma apostila completa, didática e com alto valor visual sobre o tema: "{clean_title}" no nicho "{niche}".

A apostila DEVE conter:
1. "meta": título, subtítulo, nicho, autor ("Equipe Didática"), edição ("Edição 2026 - Reta Final").
2. "study_slides": Lista com 4 slides de Onboarding ("Como Estudar Este Material"):
   - Slide 1: Boas-vindas e Visão Geral
   - Slide 2: O Ciclo de Estudo em 3 Etapas (Teoria Ativa -> Esquematização -> Prática)
   - Slide 3: Técnica Pomodoro & Gestão do Tempo
   - Slide 4: Checklist de Rendimento Diário
   Cada slide com: title, description, key_points (lista), icon_hint ("rocket", "cycle", "clock", "check").
3. "study_flowchart": 4 Fases do Fluxograma de Estudos:
   - Cada fase com: phase_number (1 a 4), title, timeframe (ex: 'Dias 1 a 3'), objective, action_steps (lista).
4. "chapters": Pelo menos 4 capítulos didáticos completos.
   - Cada capítulo com: chapter_number, title, summary, sections (lista com section_title, content_paragraphs [lista], tip_box, warning_box).
5. "study_checklist": 8 itens práticos para o aluno marcar conforme conclui os estudos.

Retorne OBRIGATORIAMENTE um JSON válido com esta exata estrutura.
"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Você é um criador de apostilas didáticas profissionais e esquematizadas. Responda apenas com o JSON estruturado."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        return None

    def _generate_native_visual_ebook(
        self,
        title: str,
        niche: str,
        target_audience: Optional[str]
    ) -> Dict[str, Any]:
        """
        Motor nativo que estrutura uma apostila completa com slides do método de estudos,
        fluxograma de aprendizagem em 4 fases e capítulos detalhados.
        """
        clean_title = re.sub(r'^(Apostila/Guia Prático:\s*|Super Combo\s*|Guia\s*)', '', title, flags=re.IGNORECASE).strip()

        # Slides de Método de Estudo
        slides = [
            {
                "id": "slide_1",
                "slide_number": 1,
                "title": "🚀 Boas-Vindas ao Método Acelerado",
                "subtitle": "Como extrair 100% de aproveitamento deste material prático",
                "description": (
                    f"Parabéns por dar este passo importante! Este material sobre {clean_title} foi concebido com uma filosofia clara: "
                    "eliminar 80% das teorias desnecessárias e focar exclusivamente nos 20% práticos que geram resultados imediatos."
                ),
                "key_points": [
                    "Conteúdo 100% esquematizado para leitura no celular ou tablet",
                    "Aplicação prática sem enrolação acadêmica",
                    "Focado em memorização de longo prazo e resolução rápida de problemas"
                ],
                "icon": "sparkles"
            },
            {
                "id": "slide_2",
                "slide_number": 2,
                "title": "🧠 O Ciclo de Estudo em 3 Etapas",
                "subtitle": "A estrutura de aprendizagem mais eficiente para adultos",
                "description": (
                    "Estudos mostram que apenas ler passivamente gera menos de 20% de retenção após 48 horas. "
                    "Para dominar o conteúdo, siga rigorosamente as 3 etapas abaixo a cada capítulo:"
                ),
                "key_points": [
                    "Etapa 1 (Leitura Ativa): Destaque palavras-chave e conceitos centrais",
                    "Etapa 2 (Esquematização): Consulte os quadros de resumo e fluxogramas",
                    "Etapa 3 (Aplicação Prática): Execute os checklists de ação ao final de cada módulo"
                ],
                "icon": "refresh-cw"
            },
            {
                "id": "slide_3",
                "slide_number": 3,
                "title": "⏱️ Gestão de Foco & Curva de Retenção",
                "subtitle": "Estude menos tempo com o dobro de absorção",
                "description": (
                    "Evite maratonas exaustivas. O cérebro humano absorve melhor informações densas em blocos focados de 25 minutos "
                    "(Técnica Pomodoro) intercalados com pausas estratégicas de 5 minutos."
                ),
                "key_points": [
                    "Sessões curtas de 25 minutos com zero distrações (celular no modo silencioso)",
                    "Revise os pontos-chave 24 horas após a primeira leitura",
                    "Faça uma recapitulação rápida de 10 minutos após 7 dias para fixação permanente"
                ],
                "icon": "clock"
            },
            {
                "id": "slide_4",
                "slide_number": 4,
                "title": "📋 Checklist Diário de Rendimento",
                "subtitle": "Seu compromisso de progresso constante",
                "description": (
                    "A consistência supera a intensidade. Não tente absorver tudo em uma única noite. "
                    "Dedique apenas 20 a 30 minutos por dia seguindo o fluxograma deste material para ver a transformação completa."
                ),
                "key_points": [
                    "Defina um horário fixo de estudo no seu dia (manhã ou noite)",
                    "Marque as caixas de verificação no checklist ao final do material",
                    "Compartilhe suas dúvidas e aplique o conhecimento na prática imediatamente"
                ],
                "icon": "check-circle"
            }
        ]

        # Fluxograma de Estudos (Roadmap em 4 Fases)
        flowchart = [
            {
                "phase_number": 1,
                "title": "Fase 1: Diagnóstico & Fundamentos",
                "timeframe": "Dias 1 a 3 (Base Sólida)",
                "objective": f"Compreender o cenário atual e mapear os principais pilares de {clean_title}.",
                "badge_color": "purple",
                "action_steps": [
                    "Leitura atenta dos Capítulos 1 e 2",
                    "Identificação dos erros clássicos que travam 90% das pessoas",
                    "Preenchimento do autodiagnóstico inicial"
                ]
            },
            {
                "phase_number": 2,
                "title": "Fase 2: O Método Passo a Passo",
                "timeframe": "Dias 4 a 10 (Execução Guiada)",
                "objective": "Aplicar o núcleo prático da apostila com ferramentas e exemplos reais.",
                "badge_color": "blue",
                "action_steps": [
                    "Implementação do roteiro detalhado do Capítulo 3",
                    "Consulta diária aos esquemas visuais e tabelas de consulta rápida",
                    "Primeiros testes de validação no seu dia a dia"
                ]
            },
            {
                "phase_number": 3,
                "title": "Fase 3: Simulação & Blindagem de Erros",
                "timeframe": "Dias 11 a 20 (Refinamento & Prática)",
                "objective": "Eliminar armadilhas, consolidar a segurança e resolver cenários difíceis.",
                "badge_color": "emerald",
                "action_steps": [
                    "Estudo dos casos de pegadinhas e pontos críticos no Capítulo 4",
                    "Exercícios e simulações práticas de fixação",
                    "Ajustes de rota conforme os resultados obtidos"
                ]
            },
            {
                "phase_number": 4,
                "title": "Fase 4: Maestria & Rotina Contínua",
                "timeframe": "Dias 21+ (Resultados Definitivos)",
                "objective": "Transformar o conhecimento adquirido em hábito sustentável e permanente.",
                "badge_color": "amber",
                "action_steps": [
                    "Conclusão do checklist final de validação",
                    "Revisão rápida semanal dos pontos-chave",
                    "Manutenção da consistência e acompanhamento de metas"
                ]
            }
        ]

        # Capítulos Estruturados da Apostila
        chapters = [
            {
                "chapter_number": 1,
                "title": f"Capítulo 1: Panorama Geral & Os Fundamentos de {clean_title}",
                "summary": "Neste primeiro módulo, desmistificamos os principais mitos e estabelecemos a base indispensável para seu progresso.",
                "sections": [
                    {
                        "section_title": "1.1 Por onde começar e por que o método tradicional falha",
                        "content_paragraphs": [
                            f"Quando a maioria das pessoas decide buscar sobre {clean_title}, elas cometem quase sempre o mesmo erro: tentam consumir volumes astronômicos de informações dispersas pela internet sem um filtro de qualidade.",
                            "O excesso de conteúdo não gera clareza — gera paralisia por análise. Para obter resultados consistentes, você precisa de um caminho linear, onde cada conceito construa o alicerce para o próximo passo."
                        ],
                        "tip_box": f"Foque apenas no essencial para o seu momento. Não tente aprender exceções complexas antes de dominar a regra básica de {clean_title}.",
                        "warning_box": "Cuidado com soluções mágicas ou promessas de resultados imediatos sem esforço. Todo processo sólido exige método e disciplina.",
                        "key_takeaway": "Menos é mais: priorize profundidade e clareza sobre quantidade de páginas."
                    },
                    {
                        "section_title": "1.2 Os 3 Pilares Inegociáveis do Sucesso",
                        "content_paragraphs": [
                            "Todo resultado de excelência neste nicho apoia-se em três pilares fundamentais:",
                            "1. **Clareza de Metas:** Saber exatamente onde você está e qual é o próximo marco concreto a ser alcançado.\n"
                            "2. **Rotina Estruturada:** Criar um ambiente livre de atritos onde a execução aconteça de forma quase automática.\n"
                            "3. **Feedback Rápido:** Avaliar periodicamente seus acertos e corrigir falhas antes que se tornem vícios difíceis de erradicar."
                        ],
                        "tip_box": "Escreva seus objetivos em um papel visível ao lado do seu computador ou mesa de estudos.",
                        "warning_box": "Não pule etapas: tentar queimar etapas é o motivo número 1 de desistência nos primeiros 15 dias.",
                        "key_takeaway": "Constância bate talento em 100% das vezes no longo prazo."
                    }
                ]
            },
            {
                "chapter_number": 2,
                "title": f"Capítulo 2: O Método Passo a Passo & Aplicação Prática",
                "summary": "O roteiro central do material: aqui você aprende a técnica detalhada com esquemas diretos ao ponto.",
                "sections": [
                    {
                        "section_title": "2.1 O Roteiro Estratégico de Execução",
                        "content_paragraphs": [
                            f"Agora que você compreende a base, vamos ao coração prático de {clean_title}. Este roteiro foi desenhado para ser executado de forma sequencial.",
                            "Siga cada instrução passo a passo, registrando suas anotações e dúvidas no caderno ou bloco de notas digital."
                        ],
                        "tip_box": "Use marcadores coloridos para categorizar os tópicos: verde para conceitos dominados, amarelo para revisão e vermelho para dúvidas urgentes.",
                        "warning_box": "Não avance para a próxima seção sem ter compreendido os exemplos práticos desta etapa.",
                        "key_takeaway": "A maestria nasce da repetição consciente de fundamentos bem executados."
                    },
                    {
                        "section_title": "2.2 Tabelas e Esquemas de Consulta Rápida",
                        "content_paragraphs": [
                            "Para facilitar sua rotina diária, sintetizamos as melhores práticas em regras mnemônicas e estruturas visuais de fácil consulta no celular.",
                            "Salve esta página nos seus favoritos ou tire prints para consultar sempre que tiver dúvidas em campo."
                        ],
                        "tip_box": "Consulte este resumo visual antes de iniciar sua sessão diária de trabalho ou estudos.",
                        "warning_box": "Não confie apenas na memória imediata; consulte o esquema sempre que necessário.",
                        "key_takeaway": "Materiais visuais aceleram o tempo de tomada de decisão em até 60%."
                    }
                ]
            },
            {
                "chapter_number": 3,
                "title": "Capítulo 3: Casos Reais, Armadilhas e Pegadinhas Comuns",
                "summary": "Identifique com antecedência os pontos críticos onde a maioria perde tempo ou comete erros graves.",
                "sections": [
                    {
                        "section_title": "3.1 As 5 Maiores Armadilhas Identificadas na Prática",
                        "content_paragraphs": [
                            "Muitos estudantes e profissionais perdem semanas preciosas por caírem em armadilhas previsíveis e evitáveis.",
                            "Analisamos dezenas de casos reais para compilar os 5 erros mais recorrentes e como você pode se blindar contra cada um deles com antecedência."
                        ],
                        "tip_box": "Mantenha um diário de erros: anotou uma falha hoje, nunca mais cometa amanhã.",
                        "warning_box": "Evite o perfeccionismo paralisante: feito com qualidade é infinitamente superior ao perfeito nunca finalizado.",
                        "key_takeaway": "Aprender com os erros dos outros é a forma mais barata e rápida de evoluir."
                    }
                ]
            },
            {
                "chapter_number": 4,
                "title": "Capítulo 4: Plano de Ação Imediato para os Próximos 7 Dias",
                "summary": "Seu cronograma de implementação prática a partir de hoje.",
                "sections": [
                    {
                        "section_title": "4.1 Seu Roteiro de 7 Dias para Resultados Concretos",
                        "content_paragraphs": [
                            "Conhecimento sem ação é apenas ilusão. Para garantir que você transforme esta leitura em realidade palpável, estruturamos seu plano para a primeira semana:",
                            "• **Dia 1 e 2:** Organização do ambiente e diagnóstico dos pontos críticos.\n"
                            "• **Dia 3 e 4:** Aplicação dos primeiros 3 passos do roteiro prático.\n"
                            "• **Dia 5 e 6:** Revisão dos esquemas visuais e eliminação das dúvidas.\n"
                            "• **Dia 7:** Avaliação dos resultados e planejamento do ciclo seguinte."
                        ],
                        "tip_box": "Comemore pequenas vitórias diárias para manter o cérebro motivado e engajado.",
                        "warning_box": "Não deixe para amanhã: a primeira ação deve ser executada nas próximas 2 horas após a leitura.",
                        "key_takeaway": "O seu futuro é moldado pelas ações de hoje, não pelas intenções de amanhã."
                    }
                ]
            }
        ]

        # Checklist de Validação Final
        checklist = [
            f"Li atentamente os slides de orientação e compreendi o ciclo de estudo em 3 etapas",
            f"Defini meu horário diário de 25 a 30 minutos focado em {clean_title}",
            "Completei a leitura ativa do Capítulo 1 e anotei os conceitos-chave",
            "Mapeei os 3 pilares fundamentais no meu cenário pessoal",
            "Estudei o roteiro prático do Capítulo 2 e consultei as tabelas esquematizadas",
            "Identifiquei as armadilhas comuns do Capítulo 3 para evitar tropeços",
            "Iniciei o plano de ação de 7 dias com a primeira tarefa já executada",
            "Revisei os esquemas visuais para fixar o aprendizado na memória de longo prazo"
        ]

        return {
            "meta": {
                "title": f"Apostila & Guia Prático: {clean_title}",
                "subtitle": f"Método Esquematizado com Slides de Orientação e Fluxograma de Estudos em 4 Fases",
                "niche": niche,
                "author": "Equipe de Especialistas LowTicket",
                "edition": "Edição Atualizada 2026 - Reta Final",
                "format": "E-book Interativo & Apostila Imprimível"
            },
            "study_slides": slides,
            "study_flowchart": flowchart,
            "chapters": chapters,
            "study_checklist": checklist
        }

ebook_generator = EbookGeneratorService()
