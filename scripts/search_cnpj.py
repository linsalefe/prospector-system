# scripts/search_cnpj.py
import sys
sys.path.append('.')

from scrapers.local_cnpj_search import LocalCNPJSearch

if __name__ == "__main__":
    import sys
    nome = " ".join(sys.argv[1:]) or "INVESTLAR"
    
    print(f"\n🔍 Buscando: {nome}")
    print("=" * 50)
    
    resultado = LocalCNPJSearch.melhor_match(nome)
    
    if resultado:
        print(f"✅ Encontrado!")
        print(f"   CNPJ: {resultado['cnpj']}")
        print(f"   Razão Social: {resultado['razao_social']}")
        print(f"   Similaridade: {resultado['score']*100:.1f}%")
        
        if resultado.get('telefone'):
            print(f"   📱 Telefone: {resultado['telefone']}")
        else:
            print(f"   📱 Telefone: Não encontrado")
        
        if resultado.get('email'):
            print(f"   📧 Email: {resultado['email']}")
        else:
            print(f"   📧 Email: Não encontrado")
        
        if resultado.get('municipio'):
            print(f"   📍 Município: {resultado['municipio']}/{resultado.get('uf', '')}")
    else:
        print("❌ Não encontrado")