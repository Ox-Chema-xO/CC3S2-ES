#!/usr/bin/env python3
import os
import zlib
import json
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple
import heapq


class GitDAGAnalyzer:
    def __init__(self, git_dir: str = '.git'):
        self.git_dir = git_dir
        self.objects_dir = os.path.join(git_dir, 'objects')
        self.commits: Dict[str, dict] = {}
        self.dag: Dict[str, List[str]] = defaultdict(list)
        self.reverse_dag: Dict[str, List[str]] = defaultdict(list)

    def read_git_object(self, sha: str) -> Tuple[str, bytes]:
        """lectura y descompresion de objetos git"""
        obj_path = os.path.join(self.objects_dir, sha[:2], sha[2:])
        if not os.path.exists(obj_path):
            raise FileNotFoundError(f"objecto {sha} no encontrado")
        with open(obj_path, 'rb') as f:
            compressed_data = f.read()
        decompressed_data = zlib.decompress(compressed_data)
        header_end = decompressed_data.find(b'\0')
        header = decompressed_data[:header_end].decode('ascii')
        content = decompressed_data[header_end + 1:]
        obj_type = header.split()[0]
        return obj_type, content

    def parse_commit(self, content: bytes) -> dict:
        """parseo a objeto commit y extraer parents"""
        lines = content.decode('utf-8').split('\n')
        commit_data = {
            'parents': [],
            'tree': '',
            'author': '',
            'committer': '',
            'message': ''
        }
        message_start = False
        for line in lines:
            if message_start:
                commit_data['message'] += line + '\n'
            elif line.startswith('parent '):
                commit_data['parents'].append(line.split()[1])
            elif line.startswith('tree '):
                commit_data['tree'] = line.split()[1]
            elif line.startswith('author '):
                commit_data['author'] = line[7:]
            elif line.startswith('committer '):
                commit_data['committer'] = line[10:]
            elif line == '':
                message_start = True
        return commit_data

    def get_all_commits(self) -> Set[str]:
        """obtenemos todos los commits sha del directorio"""
        commits = set()
        for subdir in os.listdir(self.objects_dir):
            if len(subdir) == 2 and subdir != 'info' and subdir != 'pack':
                subdir_path = os.path.join(self.objects_dir, subdir)
                if os.path.isdir(subdir_path):
                    for obj_file in os.listdir(subdir_path):
                        sha = subdir + obj_file
                        try:
                            obj_type, content = self.read_git_object(sha)
                            if obj_type == 'commit':
                                commits.add(sha)
                        except:
                            continue
        return commits

    def build_dag(self):
        """contruimos dag de los commits"""
        all_commits = self.get_all_commits()
        for sha in all_commits:
            try:
                obj_type, content = self.read_git_object(sha)
                if obj_type == 'commit':
                    commit_data = self.parse_commit(content)
                    self.commits[sha] = commit_data
                    for parent in commit_data['parents']:
                        self.dag[sha].append(parent)
                        self.reverse_dag[parent].append(sha)
            except Exception as e:
                print(f"error procesando commit {sha}: {e}")
                continue

    def get_head_commit(self) -> str:
        """obtener el head del commit"""
        head_path = os.path.join(self.git_dir, 'HEAD')
        with open(head_path, 'r') as f:
            head_content = f.read().strip()
        if head_content.startswith('ref: '):
            ref_path = os.path.join(self.git_dir, head_content[5:])
            if os.path.exists(ref_path):
                with open(ref_path, 'r') as f:
                    return f.read().strip()
        return head_content

    def calculate_depths(self, head: str) -> Dict[str, int]:
        """calculamos la profundidad usando bfs"""
        depths = {head: 0}
        queue = deque([head])
        while queue:
            current = queue.popleft()
            current_depth = depths[current]
            for parent in self.dag.get(current, []):
                if parent not in depths:
                    depths[parent] = current_depth + 1
                    queue.append(parent)
        return depths

    def calculate_branch_density(self, head: str) -> float:
        """calculamos la densidad de cada rama"""
        depths = self.calculate_depths(head)
        # grupo de commits por profundidad de nivel
        levels = defaultdict(int)
        for commit, depth in depths.items():
            levels[depth] += 1
        if not levels:
            return 0
        density_sum = 0
        total_levels = len(levels)
        for level, count in levels.items():
            if level > 0:  # saltamos nivel cero por que es del head
                density_sum += count / level
        return density_sum / total_levels if total_levels > 0 else 0

    def get_merge_debt(self, commit: str) -> int:
        """1 si es merge 0 caso contrario"""
        if len(self.commits.get(commit, {}).get('parents', [])) > 1:
            return 1
        else:
            return 0

    def find_critical_path(self, head: str) -> List[str]:
        """encontramos ruta critica usando dikjstra pra el merge"""
        root_candidates = []
        for commit in self.commits:
            if not self.dag.get(commit, []):
                root_candidates.append(commit)
        if not root_candidates:
            return [head]
        distances = {head: 0}
        previous = {}
        visited = set()
        pq = [(0, head)]
        while pq:
            current_dist, current = heapq.heappop(pq)
            if current in visited:
                continue
            visited.add(current)
            if current in root_candidates:
                path = []
                node = current
                while node is not None:
                    path.append(node)
                    node = previous.get(node)
                return path[::-1]
            for parent in self.dag.get(current, []):
                if parent in visited:
                    continue
                new_dist = current_dist + self.get_merge_debt(parent)
                if parent not in distances or new_dist < distances[parent]:
                    distances[parent] = new_dist
                    previous[parent] = current
                    heapq.heappush(pq, (new_dist, parent))
        return [head]

    def find_bottleneck_commits(self, k: int = 5) -> List[str]:
        """identificamos los commits con mayor indegree (>=2)"""
        indegrees = defaultdict(int)
        # calculamos indegree para cada commit
        for commit in self.commits:
            for parent in self.dag.get(commit, []):
                indegrees[parent] += 1
        # filtramos commits con indegree >= 2 y los ordenamos por su indegree
        bottlenecks = [(indegree, commit) for commit, indegree in indegrees.items() if indegree >= 2]
        bottlenecks.sort(reverse=True)
        return [commit for _, commit in bottlenecks[:k]]

    def generate_analysis(self) -> dict:
        """generamos analisis completo del repo"""
        self.build_dag()
        head = self.get_head_commit()
        density = self.calculate_branch_density(head)
        critical_path = self.find_critical_path(head)
        bottlenecks = self.find_bottleneck_commits(5)
        return {
            'density': density,
            'critical_path': critical_path,
            'bottlenecks': bottlenecks
        }

    def generate_dot_file(self, filename: str = 'git_graph.dot'):
        """generamos dot file para visualizar con graphviz"""
        with open(filename, 'w') as f:
            f.write('digraph GitGraph {\n')
            f.write('rankdir=TB;\n')
            f.write('node [shape=circle];\n')
            for commit in self.commits:
                short_sha = commit[:7]
                is_merge = len(self.commits[commit]['parents']) > 1
                color = 'red' if is_merge else 'lightblue'
                f.write(f' "{short_sha}" [fillcolor={color}, style=filled];\n')
            for commit in self.commits:
                short_sha = commit[:7]
                for parent in self.dag.get(commit, []):
                    parent_short = parent[:7]
                    f.write(f'  "{short_sha}" -> "{parent_short}";\n')
            f.write('}\n')


def main():
    analyzer = GitDAGAnalyzer()
    try:
        analysis = analyzer.generate_analysis()
        # guardamos el analisis en un json
        with open('git_analysis.json', 'w') as f:
            json.dump(analysis, f, indent=2)
        # generamos dot file
        analyzer.generate_dot_file()
        print("Analisis completado:")
        print(f"densidad de ramas: {analysis['density']:.4f}")
        print(f"ruta critica: {len(analysis['critical_path'])}")
        print(f"bottleneck: {len(analysis['bottlenecks'])}")
    except Exception as e:
        print(f"error durante el analisis: {e}")


if __name__ == "__main__":
    main()
