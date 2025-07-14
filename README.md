# CC3S2-ES
El proposito de este proyecto es simular una plataforma interna de analisis y ejecucion de tareas criticas.
Se requiere extraer informacion profunda de la estructura del repositorio Git, mas alla de comandos de alto nivel(git log),
trabajando directamente con los objetos internos para obtener metricas avanzadas como densidad, caminos criticos,
analisis de merges.

Aplicando conocimientos de estructura interna de Git, algoritmo Dijkstra para recorrer DAG de commits, hallar caminos
de deuda de merges de forma optima y obtener metricas.

Por lo cual implementamos `git_graph.py` que realiza:
- Lectura "raw" de objetos: El codigo abre y parsea archivos en .git/objects/<xx>/<yyyy...> usando la libreria zlib para
descomprimir blobs y commits.

- Construccion de DAG: Cada objeto commit expone la lista de padres, construye un grafo dirigido donde los nodos
son SHA-1 de commits y las aristas apuntas a sus padres.

- Metricas: densidad de ramas, critical path y top-k bottleneck commits

Al ejecutar este algoritmo `git_graph.py` se genera git_analysis.json con campos { density: float, critical_path:[sha...], bottlenecks: [sha...]}
y se crea git_graph.dot en formato DOT para visualizar con Graphviz

Referencias:
- https://www.w3schools.com/dsa/dsa_algo_graphs_dijkstra.php
- https://learn.microsoft.com/en-us/archive/msdn-magazine/2017/june/devops-git-internals-for-visual-studio-developers
- https://github.com/kapumota/DS/blob/main/2025-1/Lectura11.md
- https://www.atlassian.com/git/tutorials/git-log
