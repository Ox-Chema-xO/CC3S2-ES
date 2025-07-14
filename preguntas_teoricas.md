
1.- Por que Git es un DAG:

- En `git_graph.py` podemos notar como cada commit apunta a sus padres mediante SHA-1 hashes
en el metodo `build_dag` lo cual hace imposible que se formen
ciclos, esto garantiza que el historial de commits tenga un punto de inicio bien definido y evolucione de forma lineal o ramificada.

- El que no haya ciclos nos garantiza tener el punto de inicio bien definido y no tener rutas infinitas por lo cual nuestros algoritmos de busquedas de rutas siempre terminaran.
Por ejemplo, en `calculate_depths()` evitamos revisitar nodos y en `find_critical_path()` evitamos ciclos infinitos.
