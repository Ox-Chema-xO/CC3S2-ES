for dir in src/ tests; do
    if [ ! -d "$dir" ]; then
        echo "Error: No existe $dir"
        exit 1
    fi
done

echo "Ejecutando flake8 para estilo de codigo de git_graph en src/ "
if ! flake8 src/; then
    exit 1
fi

echo "Ejecutando shellcheck en scripts/"
for script in scripts/*.sh; do
    if [ -f "$script" ]; then
        if ! shellcheck "$script"; then
            exit 1
        fi
    fi
done

if ! pytest --maxfail=1 -disable-warnings -q --cov=src --cov-report=xml
    exit 1
fi

if [ ! -f "coverage.xml" ]; then
    echo "Error: No se genero reporte de cobertura"
    exit 1
fi

echo "Pruebas finalizadas correctamente con reporte de cobertura y resultados"
