import math
import matplotlib.pyplot as plt
import numpy as np

n = [10, 20, 50, 100, 200, 500, 1000]

data = {
    2:   [2.0, 2.0, 3.0, 4.0, 4.0, 5.0, 4.9],
    4:   [2.0, 2.0, 2.0, 3.0, 3.0, 3.0, 4.0],
    10:  [1.0, 1.0, 2.0, 2.0, 2.0, 2.9, 3.0],
    20:  [1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0],
    100: [1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0],
}

fig, axes = plt.subplots(len(data), 1, figsize=(8, 12), sharex=True)

for ax, (d, values) in zip(axes, data.items()):
    # Measured data
    ax.plot(n, values, marker="o", label="Measured")

    # ceil(log_d(n))
    log_vals = [math.ceil(math.log(ni, d)) for ni in n]
    ax.plot(n, log_vals, linestyle="--", marker="s", label=r"$\lceil \log_d(n) \rceil$")

    ax.set_xscale("log")
    ax.set_xlabel("Number of records")
    ax.set_ylabel("Average tree accesses")
    ax.set_title(f"d = {d}")
    ax.grid(True, which="both", linestyle="--", alpha=0.6)
    ax.legend()

axes[-1].set_xlabel("n")
plt.tight_layout()
plt.show()

# n values
n_values = np.array([10, 20, 50, 100, 200, 500, 1000])

# Table 1 (before reorganization)
table1 = {
    2: [4, 14, 55, 124, 252, 634, 1242],
    4: [3, 16, 45, 110, 226, 549, 1082],
    10: [1, 12, 47, 96, 199, 496, 997],
    20: [1, 9, 45, 96, 191, 499, 982],
    100: [1, 15, 36, 93, 193, 489, 960]
}

# Table 2 (after reorganization)
table2 = {
    2: [5, 8, 21, 43, 81, 205, 396],
    4: [4, 6, 13, 26, 52, 122, 238],
    10: [2, 3, 9, 17, 33, 79, 152],
    20: [2, 3, 8, 14, 26, 64, 124],
    100: [2, 3, 6, 11, 21, 53, 104]
}

# Plotting
fig, axs = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

# Colors and markers
colors = ['r', 'g', 'b', 'c', 'm']
markers = ['o', 's', 'D', '^', 'v']

# Table 1
for i, d in enumerate(table1.keys()):
    axs[0].plot(n_values, table1[d], marker=markers[i], color=colors[i], label=f'd={d}')
axs[0].set_xscale('log')
axs[0].set_xlabel('n')
axs[0].set_ylabel('Access Count')
axs[0].set_title('Before Reorganization')
axs[0].legend()
axs[0].grid(True, which='both', linestyle='--', alpha=0.5)

# Table 2
for i, d in enumerate(table2.keys()):
    axs[1].plot(n_values, table2[d], marker=markers[i], color=colors[i], label=f'd={d}')
axs[1].set_xscale('log')
axs[1].set_xlabel('n')
axs[1].set_title('After Reorganization')
axs[1].legend()
axs[1].grid(True, which='both', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.show()

# n values
n_values = [10, 20, 50, 100, 200, 500, 1000]

# tree reads for each d
reads = {
    2: [4.11, 4.32, 4.84, 5.16, 5.31, 6.51, 6.35],
    4: [2.93, 3.18, 3.63, 3.71, 3.59, 4.57, 4.85],
    10: [2.12, 2.20, 2.43, 2.42, 2.47, 3.39, 3.39],
    20: [1.78, 1.87, 2.08, 2.22, 2.30, 2.37, 2.34],
    100: [1.00, 1.00, 1.00, 1.00, 1.98, 2.04, 2.02]
}

# tree writes for each d
writes = {
    2: [2.72, 2.67, 2.87, 2.70, 2.91, 3.18, 3.03],
    4: [1.96, 2.01, 2.28, 2.07, 1.88, 2.54, 2.21],
    10: [1.42, 1.38, 1.65, 1.70, 1.75, 1.59, 1.60],
    20: [1.18, 1.18, 1.16, 1.41, 1.51, 1.49, 1.51],
    100: [1.00, 1.00, 1.00, 1.00, 1.02, 1.08, 1.04]
}

# colors for consistency
colors = {2:'blue', 4:'green', 10:'orange', 20:'red', 100:'purple'}

plt.figure(figsize=(12, 6))

# plot both reads and writes
for d in reads:
    plt.plot(n_values, reads[d], marker='o', linestyle='-', color=colors[d], label=f'd={d} reads')
    plt.plot(n_values, writes[d], marker='x', linestyle='--', color=colors[d], label=f'd={d} writes')

plt.xscale('log')
plt.xlabel('n')
plt.ylabel('Access count')
plt.title('Tree reads and writes for different d values (ADD test)')
plt.legend()
plt.grid(True, which="both", ls="--")
plt.show()

# n values
n_values = [20, 50, 100, 200, 500, 1000, 2000]

# Tree reads
tree_reads = {
    2: [2.60, 3.80, 3.60, 4.60, 5.80, 5.40, 6.00],
    4: [3.00, 2.20, 3.20, 3.00, 3.40, 4.40, 4.00],
    10: [1.00, 2.20, 2.20, 2.00, 3.00, 3.40, 3.00],
    20: [2.00, 2.60, 2.00, 2.00, 2.00, 2.20, 3.00],
    100: [2.00, 2.00, 2.00, 1.00, 2.00, 2.00, 2.00]
}

# Tree writes
tree_writes = {
    2: [1.80, 2.10, 2.10, 2.30, 2.10, 1.70, 1.30],
    4: [2.40, 1.50, 1.40, 1.00, 1.60, 1.70, 1.10],
    10: [1.00, 1.50, 1.20, 1.00, 1.10, 1.60, 1.10],
    20: [1.00, 1.90, 1.00, 1.00, 1.10, 1.30, 1.00],
    100: [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]
}

# Plotting
plt.figure(figsize=(12, 6))

for d in tree_reads:
    plt.plot(n_values, tree_reads[d], marker='o', label=f"d={d} reads")
    plt.plot(n_values, tree_writes[d], marker='x', linestyle='--', label=f"d={d} writes")

plt.xlabel("Number of elements (n)")
plt.ylabel("Average access count")
plt.title("Tree reads and writes for different d values (DELETE test)")
plt.legend()
plt.grid(True)
plt.show()
