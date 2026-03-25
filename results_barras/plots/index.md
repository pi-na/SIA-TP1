# Bar Plot Manifest

## BFS vs A* (allow deadlocks)
- Mode: `level`
- Sources: `results_optimal_allow_deadlocks/summary/benchmark_summary.csv`
- [bfs_vs_a_star_allow_time_seconds_by_level.png](./bfs_vs_a_star_allow_time_seconds_by_level.png)
- [bfs_vs_a_star_allow_frontier_count_by_level.png](./bfs_vs_a_star_allow_frontier_count_by_level.png)
- [bfs_vs_a_star_allow_nodes_expanded_by_level.png](./bfs_vs_a_star_allow_nodes_expanded_by_level.png)
- [bfs_vs_a_star_allow_cost_by_level.png](./bfs_vs_a_star_allow_cost_by_level.png)

## BFS (prune) vs A* (allow)
- Mode: `level`
- Sources: `results_optimal_bfs_prune_deadlocks/summary/benchmark_summary.csv`
- [bfs_vs_a_star_prune_time_seconds_by_level.png](./bfs_vs_a_star_prune_time_seconds_by_level.png)
- [bfs_vs_a_star_prune_frontier_count_by_level.png](./bfs_vs_a_star_prune_frontier_count_by_level.png)
- [bfs_vs_a_star_prune_nodes_expanded_by_level.png](./bfs_vs_a_star_prune_nodes_expanded_by_level.png)
- [bfs_vs_a_star_prune_cost_by_level.png](./bfs_vs_a_star_prune_cost_by_level.png)

## DFS (allow) vs Greedy (allow)
- Mode: `level`
- Sources: `results_dfs_allow_deadlocks/summary/benchmark_summary.csv`
- [dfs_vs_greedy_allow_time_seconds_by_level.png](./dfs_vs_greedy_allow_time_seconds_by_level.png)
- [dfs_vs_greedy_allow_frontier_count_by_level.png](./dfs_vs_greedy_allow_frontier_count_by_level.png)
- [dfs_vs_greedy_allow_nodes_expanded_by_level.png](./dfs_vs_greedy_allow_nodes_expanded_by_level.png)
- [dfs_vs_greedy_allow_cost_by_level.png](./dfs_vs_greedy_allow_cost_by_level.png)

## DFS (prune) vs Greedy (allow)
- Mode: `level`
- Sources: `results_dfs_prune_deadlocks/summary/benchmark_summary.csv`
- [dfs_vs_greedy_prune_time_seconds_by_level.png](./dfs_vs_greedy_prune_time_seconds_by_level.png)
- [dfs_vs_greedy_prune_frontier_count_by_level.png](./dfs_vs_greedy_prune_frontier_count_by_level.png)
- [dfs_vs_greedy_prune_nodes_expanded_by_level.png](./dfs_vs_greedy_prune_nodes_expanded_by_level.png)
- [dfs_vs_greedy_prune_cost_by_level.png](./dfs_vs_greedy_prune_cost_by_level.png)

## Greedy vs A* (allow deadlocks)
- Mode: `level`
- Sources: `results_greedy_vs_a_star/summary/benchmark_summary.csv`
- [greedy_vs_a_star_allow_time_seconds_by_level.png](./greedy_vs_a_star_allow_time_seconds_by_level.png)
- [greedy_vs_a_star_allow_frontier_count_by_level.png](./greedy_vs_a_star_allow_frontier_count_by_level.png)
- [greedy_vs_a_star_allow_nodes_expanded_by_level.png](./greedy_vs_a_star_allow_nodes_expanded_by_level.png)
- [greedy_vs_a_star_allow_cost_by_level.png](./greedy_vs_a_star_allow_cost_by_level.png)

## BFS vs DFS (allow deadlocks)
- Mode: `level`
- Sources: `results_dfs_vs_bfs_allow_deadlocks/summary/benchmark_summary.csv`
- [bfs_vs_dfs_allow_time_seconds_by_level.png](./bfs_vs_dfs_allow_time_seconds_by_level.png)
- [bfs_vs_dfs_allow_frontier_count_by_level.png](./bfs_vs_dfs_allow_frontier_count_by_level.png)
- [bfs_vs_dfs_allow_nodes_expanded_by_level.png](./bfs_vs_dfs_allow_nodes_expanded_by_level.png)
- [bfs_vs_dfs_allow_cost_by_level.png](./bfs_vs_dfs_allow_cost_by_level.png)

## BFS vs DFS (prune deadlocks)
- Mode: `level`
- Sources: `results_dfs_vs_bfs_prune_deadlocks/summary/benchmark_summary.csv`
- [bfs_vs_dfs_prune_time_seconds_by_level.png](./bfs_vs_dfs_prune_time_seconds_by_level.png)
- [bfs_vs_dfs_prune_frontier_count_by_level.png](./bfs_vs_dfs_prune_frontier_count_by_level.png)
- [bfs_vs_dfs_prune_nodes_expanded_by_level.png](./bfs_vs_dfs_prune_nodes_expanded_by_level.png)
- [bfs_vs_dfs_prune_cost_by_level.png](./bfs_vs_dfs_prune_cost_by_level.png)

## BFS: allow vs prune
- Mode: `level`
- Sources: `results_dfs_vs_bfs_allow_deadlocks/summary/benchmark_summary.csv`, `results_dfs_vs_bfs_prune_deadlocks/summary/benchmark_summary.csv`
- [bfs_policy_sensitivity_time_seconds_by_level.png](./bfs_policy_sensitivity_time_seconds_by_level.png)
- [bfs_policy_sensitivity_frontier_count_by_level.png](./bfs_policy_sensitivity_frontier_count_by_level.png)
- [bfs_policy_sensitivity_nodes_expanded_by_level.png](./bfs_policy_sensitivity_nodes_expanded_by_level.png)
- [bfs_policy_sensitivity_cost_by_level.png](./bfs_policy_sensitivity_cost_by_level.png)

## DFS: allow vs prune
- Mode: `level`
- Sources: `results_dfs_vs_bfs_allow_deadlocks/summary/benchmark_summary.csv`, `results_dfs_vs_bfs_prune_deadlocks/summary/benchmark_summary.csv`
- [dfs_policy_sensitivity_time_seconds_by_level.png](./dfs_policy_sensitivity_time_seconds_by_level.png)
- [dfs_policy_sensitivity_frontier_count_by_level.png](./dfs_policy_sensitivity_frontier_count_by_level.png)
- [dfs_policy_sensitivity_nodes_expanded_by_level.png](./dfs_policy_sensitivity_nodes_expanded_by_level.png)
- [dfs_policy_sensitivity_cost_by_level.png](./dfs_policy_sensitivity_cost_by_level.png)

## Greedy: heuristics comparadas
- Mode: `overall`
- Sources: `results_greedy_vs_a_star/summary/benchmark_summary.csv`
- [greedy_heuristics_global_time_seconds_global.png](./greedy_heuristics_global_time_seconds_global.png)
- [greedy_heuristics_global_frontier_count_global.png](./greedy_heuristics_global_frontier_count_global.png)
- [greedy_heuristics_global_nodes_expanded_global.png](./greedy_heuristics_global_nodes_expanded_global.png)
- [greedy_heuristics_global_cost_global.png](./greedy_heuristics_global_cost_global.png)

## A*: heurísticas comparadas
- Mode: `overall`
- Sources: `results_greedy_vs_a_star/summary/benchmark_summary.csv`
- [a_star_heuristics_global_time_seconds_global.png](./a_star_heuristics_global_time_seconds_global.png)
- [a_star_heuristics_global_frontier_count_global.png](./a_star_heuristics_global_frontier_count_global.png)
- [a_star_heuristics_global_nodes_expanded_global.png](./a_star_heuristics_global_nodes_expanded_global.png)
- [a_star_heuristics_global_cost_global.png](./a_star_heuristics_global_cost_global.png)
