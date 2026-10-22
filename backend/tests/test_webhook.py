import json
import time
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_webhook_ingestion():
    print("=" * 60)
    print("🧪 INICIANDO TESTE COM O MODELO DEFINITIVO SUPABASE")
    print("=" * 60)

    # 1. Check Root Endpoint
    try:
        r = requests.get(f"{BASE_URL}/")
        print(f"✅ Root API Status: {r.status_code} - {r.json().get('status')}")
        print(f"🎯 Database Target: {r.json().get('database_target')}")
    except Exception as e:
        print(f"❌ Não foi possível conectar ao servidor em {BASE_URL}: {e}")
        return False

    # 2. Test Kiwify Format Webhook
    print("\n📦 1. Enviando Webhook formato Kiwify...")
    kiwify_payload = {
        "order_id": f"TEST-KWF-{int(time.time())}",
        "order_status": "paid",
        "order_amount": 2790,  # R$ 27,90
        "Product": {
            "product_name": "Planner Financeiro Definitivo Notion + Planilha",
            "product_id": "prod_notion_01"
        },
        "Customer": {
            "full_name": "Juliana Rocha Teste",
            "email": "juliana.teste@gmail.com",
            "mobile": "+5511988887777"
        },
        "Commissions": {
            "charge_amount": 2790,
            "my_commission": 2538
        }
    }
    
    res = requests.post(f"{BASE_URL}/api/webhooks/order", json=kiwify_payload)
    print(f"Status Code: {res.status_code}")
    print(f"Resposta Kiwify: {json.dumps(res.json(), indent=2, ensure_ascii=False)}")
    assert res.status_code == 200, "Erro no webhook da Kiwify"
    assert res.json()["status"] == "success"

    # 3. Test Hotmart Format Webhook
    print("\n📦 2. Enviando Webhook formato Hotmart...")
    hotmart_payload = {
        "data": {
            "purchase": {
                "transaction": f"TEST-HOT-{int(time.time())}",
                "status": "APPROVED",
                "price": {"value": 37.00}
            },
            "product": {
                "name": "Apostila Digital Caixa Econômica 2026 (Reta Final)"
            },
            "buyer": {
                "name": "Lucas Fernandes",
                "email": "lucas.fernandes@teste.com",
                "checkout_phone": "+5521999991111"
            }
        }
    }

    res_hotmart = requests.post(f"{BASE_URL}/api/webhooks/order", json=hotmart_payload)
    print(f"Status Code: {res_hotmart.status_code}")
    print(f"Resposta Hotmart: {json.dumps(res_hotmart.json(), indent=2, ensure_ascii=False)}")
    assert res_hotmart.status_code == 200, "Erro no webhook da Hotmart"
    assert res_hotmart.json()["status"] == "success"

    # 4. Check Updated Metrics
    print("\n📊 3. Consultando Métricas Consolidadas de Vendas...")
    metrics_res = requests.get(f"{BASE_URL}/api/orders/metrics")
    print(f"Status Code: {metrics_res.status_code}")
    metrics = metrics_res.json()
    print(f"Faturamento Bruto: R$ {metrics['total_revenue']:.2f}")
    print(f"Faturamento Líquido: R$ {metrics['net_revenue']:.2f}")
    print(f"Total de Pedidos: {metrics['total_orders']}")
    print(f"Ticket Médio: R$ {metrics['average_ticket']:.2f}")
    print(f"Por Plataforma: {metrics['orders_by_platform']}")

    # 5. Check Products with Sales
    print("\n📦 4. Verificando Produtos e Vendas Atribuídas...")
    prod_res = requests.get(f"{BASE_URL}/api/products")
    products = prod_res.json()
    for p in products:
        print(f" - [{p['status']}] {p['title']} (slug: {p['slug']}): {p['total_sales']} vendas | R$ {p['total_revenue']:.2f}")

    print("\n✨ TODOS OS TESTES PASSARAM COM SUCESSO NO MODELO SUPABASE!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_webhook_ingestion()
