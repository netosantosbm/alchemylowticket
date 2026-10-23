import json
import asyncio
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from models import Product
from app.services.ebook_generator import ebook_generator

router = APIRouter(prefix="/api/ebooks", tags=["E-books & Apostilas com Slides"])

class GenerateEbookRequest(BaseModel):
    product_id: Optional[int] = None
    title: Optional[str] = None
    niche: Optional[str] = "Geral"
    target_audience: Optional[str] = None
    save_to_product: Optional[bool] = True

def build_flowchart_html(flowchart: List[Dict[str, Any]]) -> str:
    cards = []
    for i, phase in enumerate(flowchart):
        steps_html = "".join([f"<li>{step}</li>" for step in phase.get("action_steps", [])])
        card = f"""
        <div class="phase-card">
          <div class="phase-header">
            <span class="phase-num">Fase {phase.get('phase_number', i+1)}</span>
            <span class="phase-time">{phase.get('timeframe', '')}</span>
          </div>
          <h3 class="phase-title">{phase.get('title', '')}</h3>
          <p class="phase-objective">{phase.get('objective', '')}</p>
          <ul class="phase-steps">
            {steps_html}
          </ul>
        </div>
        """
        cards.append(card)
    return "\n".join(cards)

def build_chapters_html(chapters: List[Dict[str, Any]]) -> str:
    rendered = []
    for i, chapter in enumerate(chapters):
        sections_html = []
        for sec in chapter.get("sections", []):
            paragraphs = "".join([f"<p>{p}</p>" for p in sec.get("content_paragraphs", [])])
            tip_html = f'<div class="callout callout-tip">💡 <strong>Dica de Ouro:</strong> {sec.get("tip_box")}</div>' if sec.get("tip_box") else ""
            warn_html = f'<div class="callout callout-warning">⚠️ <strong>Atenção / Armadilha:</strong> {sec.get("warning_box")}</div>' if sec.get("warning_box") else ""
            take_html = f'<div class="callout callout-takeaway">📌 <strong>Para Fixar:</strong> {sec.get("key_takeaway")}</div>' if sec.get("key_takeaway") else ""
            sec_html = f"""
            <div class="section-block">
              <h4 class="section-title">{sec.get("section_title", "")}</h4>
              {paragraphs}
              {tip_html}
              {warn_html}
              {take_html}
            </div>
            """
            sections_html.append(sec_html)
        
        chap_html = f"""
        <div class="chapter-card">
          <h3 class="chapter-title">{chapter.get("title", f"Capítulo {i+1}")}</h3>
          <p class="chapter-summary">{chapter.get("summary", "")}</p>
          {"".join(sections_html)}
        </div>
        """
        rendered.append(chap_html)
    return "\n".join(rendered)

def build_checklist_html(checklist: List[str]) -> str:
    items = []
    for item in checklist:
        items.append(f"""
        <label class="check-item">
          <input type="checkbox">
          <span>{item}</span>
        </label>
        """)
    return "\n".join(items)

@router.post("/generate")
async def generate_product_ebook(
    req: GenerateEbookRequest,
    db: Session = Depends(get_db)
):
    """
    Gera uma apostila completa com slides do método de estudos,
    fluxograma de aprendizagem e capítulos esquematizados.
    """
    product = None
    title = req.title
    niche = req.niche

    if req.product_id:
        product = db.query(Product).filter(Product.id == req.product_id).first()
        if product:
            title = title or product.title
            niche = niche or product.niche

    if not title:
        raise HTTPException(status_code=400, detail="Título ou product_id é obrigatório.")

    # Gera o material didático visual
    ebook_data = await ebook_generator.generate_ebook(
        title=title,
        niche=niche or "Geral",
        target_audience=req.target_audience,
        db=db
    )

    # Se vinculado a um produto, salva no registro
    if req.save_to_product and product:
        product.delivery_content = ebook_data
        delivery_link = f"/api/ebooks/render/{product.id}"
        if not product.delivery_url or "api/ebooks/render" in product.delivery_url:
            product.delivery_url = delivery_link
        
        db.commit()
        db.refresh(product)
        ebook_data["saved_to_product_id"] = product.id
        ebook_data["delivery_url"] = product.delivery_url

    return ebook_data

@router.get("/product/{product_id}")
def get_product_ebook_data(product_id: int, db: Session = Depends(get_db)):
    """Retorna os dados do e-book / apostila salvos para o produto."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    if not product.delivery_content:
        raise HTTPException(status_code=404, detail="Este produto ainda não possui apostila/slides gerados.")

    return {
        "product_id": product.id,
        "product_title": product.title,
        "delivery_content": product.delivery_content,
        "delivery_url": product.delivery_url
    }

@router.get("/render/{product_id}", response_class=HTMLResponse)
def render_ebook_html(product_id: int, db: Session = Depends(get_db)):
    """
    Renderiza a apostila completa em uma página HTML moderna, responsiva e pronta para impressão em PDF.
    Pode ser acessada pelo aluno diretamente como Link de Entrega da Kiwify.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    content = product.delivery_content
    if not content:
        loop = asyncio.new_event_loop()
        content = loop.run_until_complete(ebook_generator.generate_ebook(product.title, product.niche, db=db))
        product.delivery_content = content
        product.delivery_url = f"/api/ebooks/render/{product.id}"
        db.commit()

    meta = content.get("meta", {})
    slides = content.get("study_slides", [])
    flowchart = content.get("study_flowchart", [])
    chapters = content.get("chapters", [])
    checklist = content.get("study_checklist", [])

    slides_json = json.dumps(slides, ensure_ascii=False)
    flowchart_html = build_flowchart_html(flowchart)
    chapters_html = build_chapters_html(chapters)
    checklist_html = build_checklist_html(checklist)

    title_val = meta.get('title', product.title)
    edition_val = meta.get('edition', 'Edição 2026 - Reta Final')
    subtitle_val = meta.get('subtitle', 'Método Esquematizado com Slides e Fluxograma Prático')
    niche_val = meta.get('niche', product.niche)
    author_val = meta.get('author', 'Equipe Especialista')

    html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_val}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --primary: #6366f1;
      --primary-dark: #4f46e5;
      --emerald: #10b981;
      --amber: #f59e0b;
      --bg: #090d16;
      --card-bg: #111827;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --border: #1f2937;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding-bottom: 80px;
    }}

    /* Top Floating Action Bar */
    .action-bar {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(17, 24, 39, 0.9);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
    }}

    .action-title {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 14px;
      font-weight: 700;
      color: #fff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .action-buttons {{
      display: flex;
      gap: 10px;
      flex-shrink: 0;
    }}

    .btn {{
      padding: 8px 16px;
      border-radius: 10px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
      text-decoration: none;
      border: none;
    }}

    .btn-primary {{
      background: linear-gradient(135deg, #10b981, #059669);
      color: #fff;
      box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
    }}
    .btn-primary:hover {{
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
    }}

    .btn-secondary {{
      background: #1f2937;
      color: #e5e7eb;
      border: 1px solid #374151;
    }}
    .btn-secondary:hover {{
      background: #374151;
    }}

    /* Container */
    .container {{
      max-width: 900px;
      margin: 0 auto;
      padding: 32px 20px;
    }}

    /* Cover Section */
    .cover {{
      background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
      border: 1px solid #312e81;
      border-radius: 24px;
      padding: 48px 36px;
      text-align: center;
      margin-bottom: 40px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.4);
      position: relative;
      overflow: hidden;
    }}

    .badge-edition {{
      display: inline-block;
      padding: 6px 14px;
      background: rgba(99, 102, 241, 0.2);
      border: 1px solid rgba(99, 102, 241, 0.4);
      border-radius: 9999px;
      color: #a5b4fc;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 16px;
    }}

    .cover-title {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 28px;
      font-weight: 800;
      color: #ffffff;
      line-height: 1.25;
      margin-bottom: 12px;
    }}

    .cover-subtitle {{
      font-size: 14px;
      color: #cbd5e1;
      max-width: 600px;
      margin: 0 auto 24px auto;
      line-height: 1.5;
    }}

    .cover-meta {{
      font-size: 12px;
      color: #94a3b8;
      display: flex;
      justify-content: center;
      gap: 20px;
    }}

    /* Section Headers */
    .section-header {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 20px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--border);
    }}

    .section-header h2 {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 20px;
      font-weight: 700;
      color: #fff;
    }}

    /* SLIDES CAROUSEL CARD */
    .slides-wrapper {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 28px;
      margin-bottom: 40px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }}

    .slide-content {{
      min-height: 180px;
    }}

    .slide-badge {{
      display: inline-block;
      font-size: 10px;
      font-weight: 700;
      color: #6ee7b7;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 3px 10px;
      border-radius: 6px;
      margin-bottom: 10px;
      text-transform: uppercase;
    }}

    .slide-title {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 18px;
      font-weight: 700;
      color: #fff;
      margin-bottom: 6px;
    }}

    .slide-desc {{
      font-size: 13px;
      color: #cbd5e1;
      margin-bottom: 16px;
      line-height: 1.6;
    }}

    .slide-points {{
      list-style: none;
      display: grid;
      gap: 8px;
    }}

    .slide-points li {{
      font-size: 12px;
      color: #94a3b8;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .slide-points li::before {{
      content: '✓';
      color: #10b981;
      font-weight: bold;
    }}

    .slides-controls {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid rgba(255,255,255,0.08);
    }}

    .slide-indicator {{
      font-size: 12px;
      color: var(--text-muted);
      font-weight: 600;
    }}

    /* FLOWCHART ROADMAP */
    .flowchart-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-bottom: 40px;
    }}

    .phase-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 20px;
      transition: all 0.2s ease;
    }}

    .phase-card:hover {{
      border-color: #6366f1;
      transform: translateY(-2px);
    }}

    .phase-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }}

    .phase-num {{
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      padding: 3px 8px;
      border-radius: 6px;
      background: rgba(99, 102, 241, 0.2);
      color: #a5b4fc;
    }}

    .phase-time {{
      font-size: 11px;
      color: #6ee7b7;
      font-weight: 600;
    }}

    .phase-title {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 15px;
      font-weight: 700;
      color: #fff;
      margin-bottom: 8px;
    }}

    .phase-objective {{
      font-size: 12px;
      color: #94a3b8;
      margin-bottom: 14px;
      line-height: 1.5;
    }}

    .phase-steps {{
      list-style: none;
      display: grid;
      gap: 6px;
    }}

    .phase-steps li {{
      font-size: 11px;
      color: #cbd5e1;
      padding-left: 14px;
      position: relative;
    }}

    .phase-steps li::before {{
      content: '➔';
      position: absolute;
      left: 0;
      color: #6366f1;
      font-size: 10px;
    }}

    /* CHAPTERS CONTENT */
    .chapter-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 32px;
      margin-bottom: 30px;
    }}

    .chapter-title {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 20px;
      font-weight: 800;
      color: #fff;
      margin-bottom: 8px;
    }}

    .chapter-summary {{
      font-size: 13px;
      color: #94a3b8;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
      font-style: italic;
    }}

    .section-block {{
      margin-bottom: 24px;
    }}

    .section-title {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 16px;
      font-weight: 700;
      color: #e2e8f0;
      margin-bottom: 10px;
    }}

    .section-block p {{
      font-size: 13px;
      color: #cbd5e1;
      margin-bottom: 12px;
      line-height: 1.7;
      white-space: pre-line;
    }}

    /* Callout Boxes */
    .callout {{
      padding: 14px 18px;
      border-radius: 12px;
      margin: 16px 0;
      font-size: 12px;
      line-height: 1.6;
    }}

    .callout-tip {{
      background: rgba(16, 185, 129, 0.1);
      border-left: 4px solid #10b981;
      color: #d1fae5;
    }}

    .callout-warning {{
      background: rgba(245, 158, 11, 0.1);
      border-left: 4px solid #f59e0b;
      color: #fef3c7;
    }}

    .callout-takeaway {{
      background: rgba(99, 102, 241, 0.1);
      border-left: 4px solid #6366f1;
      color: #e0e7ff;
      font-weight: 600;
    }}

    /* CHECKLIST */
    .checklist-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 28px;
      margin-top: 40px;
    }}

    .check-item {{
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 10px 0;
      border-bottom: 1px solid rgba(255,255,255,0.05);
      font-size: 13px;
      color: #e2e8f0;
    }}

    .check-item input[type="checkbox"] {{
      width: 18px;
      height: 18px;
      accent-color: #10b981;
      margin-top: 2px;
      cursor: pointer;
    }}

    /* PRINT SPECIFIC STYLES (PDF EXPORT) */
    @media print {{
      body {{
        background: #ffffff !important;
        color: #1f2937 !important;
        font-size: 11pt;
        padding: 0;
      }}

      .action-bar, .slides-controls {{
        display: none !important;
      }}

      .container {{
        max-width: 100% !important;
        padding: 0 !important;
      }}

      .cover {{
        background: #f8fafc !important;
        color: #0f172a !important;
        border: 2px solid #cbd5e1 !important;
        box-shadow: none !important;
        page-break-after: always;
      }}

      .cover-title {{
        color: #0f172a !important;
      }}

      .cover-subtitle {{
        color: #475569 !important;
      }}

      .chapter-card, .slides-wrapper, .checklist-card, .phase-card {{
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        color: #1f2937 !important;
        box-shadow: none !important;
        page-break-inside: avoid;
      }}

      .chapter-title, .section-title, .slide-title, .phase-title {{
        color: #0f172a !important;
      }}

      .section-block p, .slide-desc, .phase-objective {{
        color: #334155 !important;
      }}

      .callout-tip {{
        background: #f0fdf4 !important;
        color: #166534 !important;
      }}

      .callout-warning {{
        background: #fffbeb !important;
        color: #92400e !important;
      }}

      .callout-takeaway {{
        background: #eef2ff !important;
        color: #3730a3 !important;
      }}
    }}
  </style>
</head>
<body>

  <!-- Floating Header / Action Bar -->
  <div class="action-bar">
    <div class="action-title">
      📖 {title_val}
    </div>
    <div class="action-buttons">
      <button onclick="window.print()" class="btn btn-primary">
        🖨️ Salvar como PDF / Imprimir
      </button>
      <button onclick="navigator.clipboard.writeText(window.location.href); alert('Link de Acesso copiado!')" class="btn btn-secondary">
        🔗 Copiar Link
      </button>
    </div>
  </div>

  <div class="container">
    
    <!-- Cover Page -->
    <div class="cover">
      <span class="badge-edition">{edition_val}</span>
      <h1 class="cover-title">{title_val}</h1>
      <p class="cover-subtitle">{subtitle_val}</p>
      <div class="cover-meta">
        <span>Nicho: <strong>{niche_val}</strong></span>
        <span>•</span>
        <span>Autor: <strong>{author_val}</strong></span>
      </div>
    </div>

    <!-- Onboarding Slides Section -->
    <div class="section-header">
      <h2>🖥️ Slides de Onboarding: Como Estudar Este Material</h2>
    </div>

    <div class="slides-wrapper">
      <div id="slide-container" class="slide-content">
        <!-- Rendered by JS -->
      </div>
      <div class="slides-controls">
        <button id="prev-slide" class="btn btn-secondary" onclick="prevSlide()">← Anterior</button>
        <span id="slide-counter" class="slide-indicator">Slide 1 de 4</span>
        <button id="next-slide" class="btn btn-secondary" onclick="nextSlide()">Próximo →</button>
      </div>
    </div>

    <!-- Study Flowchart Roadmap Section -->
    <div class="section-header">
      <h2>🗺️ Fluxograma de Estudos: Seu Roteiro em 4 Fases</h2>
    </div>

    <div class="flowchart-grid">
      {flowchart_html}
    </div>

    <!-- Chapters Content Section -->
    <div class="section-header">
      <h2>📄 Conteúdo Didático & Capítulos Esquematizados</h2>
    </div>

    {chapters_html}

    <!-- Study Checklist Section -->
    <div class="checklist-card">
      <div class="section-header" style="margin-bottom: 12px; border: none;">
        <h2>✅ Checklist de Conclusão & Acompanhamento</h2>
      </div>
      <p style="font-size: 13px; color: #94a3b8; margin-bottom: 20px;">
        Marque os itens conforme avança no estudo para garantir 100% de absorção prática:
      </p>
      {checklist_html}
    </div>

  </div>

  <script>
    const slidesData = {slides_json};
    let currentSlide = 0;

    function renderSlide(index) {{
      if (!slidesData || slidesData.length === 0) return;
      const slide = slidesData[index];
      const container = document.getElementById('slide-container');
      const counter = document.getElementById('slide-counter');
      
      counter.innerText = `Slide ${{index + 1}} de ${{slidesData.length}}`;

      let pointsHtml = '';
      if (slide.key_points) {{
        pointsHtml = '<ul class="slide-points">' + 
          slide.key_points.map(pt => `<li>${{pt}}</li>`).join('') + 
          '</ul>';
      }}

      container.innerHTML = `
        <span class="slide-badge">Guia de Estudos #${{slide.slide_number || index + 1}}</span>
        <h3 class="slide-title">${{slide.title}}</h3>
        <p class="slide-desc">${{slide.description}}</p>
        ${{pointsHtml}}
      `;

      document.getElementById('prev-slide').disabled = (index === 0);
      document.getElementById('next-slide').disabled = (index === slidesData.length - 1);
    }}

    function nextSlide() {{
      if (currentSlide < slidesData.length - 1) {{
        currentSlide++;
        renderSlide(currentSlide);
      }}
    }}

    function prevSlide() {{
      if (currentSlide > 0) {{
        currentSlide--;
        renderSlide(currentSlide);
      }}
    }}

    renderSlide(0);
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html_template, status_code=200)
