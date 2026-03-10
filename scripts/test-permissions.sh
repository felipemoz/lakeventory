#!/bin/bash
# Test Databricks API permissions for each collector

echo "=== Testando permissões dos coletores Lakeventory ==="
echo ""

COLLECTORS=("clusters" "sql" "mlflow" "uc" "repos" "identities" "sharing")
PYTHON="${PYTHON:-python}"

for collector in "${COLLECTORS[@]}"; do
    echo "📋 Testando: $collector"
    echo "----------------------------------------"
    
    output=$($PYTHON -m lakeventory --source sdk --collect "$collector" --log-level INFO 2>&1)
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "✅ SUCESSO - Permissões OK"
        item_count=$(echo "$output" | grep -oE '[0-9]+ items' | head -1)
        echo "   Encontrado: $item_count"
    else
        echo "❌ FALHOU"
        # Mostrar apenas linhas de erro relevantes
        echo "$output" | grep -E "ERROR|403|Forbidden|PermissionDenied|Unauthorized" | head -5
    fi
    
    echo ""
done

echo "=== Teste concluído ==="
echo ""
echo "Para detalhes completos de um coletor específico, use:"
echo "  python -m lakeventory --source sdk --collect <COLLECTOR> --log-level DEBUG"
