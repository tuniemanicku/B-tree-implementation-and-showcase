import math
import matplotlib.pyplot as plt

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
    ax.plot(n, values, marker="o", label="Measured")

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

n_values = [10, 20, 50, 100, 200, 500, 1000]

before_reorg = {
    2: [4, 21, 57, 123, 251, 625, 1242],
    4: [3, 14, 45, 105, 221, 550, 1095],
    10: [1, 13, 42, 96, 204, 507, 1007],
    20: [1, 14, 42, 91, 197, 494, 976],
    100: [1, 9, 45, 92, 192, 481, 950]
}

after_reorg = {
    2: [4, 8, 21, 43, 83, 200, 398],
    4: [3, 6, 12, 27, 50, 122, 243],
    10: [1, 3, 9, 17, 32, 78, 152],
    20: [1, 3, 8, 14, 27, 65, 124],
    100: [1, 3, 6, 11, 21, 53, 103]
}

ceiling_values = {
    2: [14, 26, 66, 131, 262, 636, 1253],
    4: [13, 24, 57, 117, 227, 559, 1104],
    10: [11, 21, 54, 107, 211, 518, 1017],
    20: [11, 21, 52, 104, 206, 506, 981],
    100: [11, 21, 50, 101, 199, 492, 961]
}

plt.figure(figsize=(15, 10))

for idx, d in enumerate(before_reorg.keys(), 1):
    plt.subplot(3, 2, idx)
    plt.plot(n_values, before_reorg[d], marker='o', label='Before Reorg')
    plt.plot(n_values, after_reorg[d], marker='s', label='After Reorg')
    plt.plot(n_values, ceiling_values[d], marker='^', label='Ceiling (rc+nc)')
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('n (number of records)')
    plt.ylabel('Access count')
    plt.title(f'd = {d}')
    plt.grid(True, which="both", ls="--", linewidth=0.5)
    plt.legend()

plt.tight_layout()
plt.show()

n_values = [10, 20, 50, 100, 200, 500, 1000]

reads = {
    2: [4.11, 4.32, 4.84, 5.16, 5.31, 6.51, 6.35],
    4: [2.93, 3.18, 3.63, 3.71, 3.59, 4.57, 4.85],
    10: [2.12, 2.20, 2.43, 2.42, 2.47, 3.39, 3.39],
    20: [1.78, 1.87, 2.08, 2.22, 2.30, 2.37, 2.34],
    100: [1.00, 1.00, 1.00, 1.00, 1.98, 2.04, 2.02]
}

writes = {
    2: [2.72, 2.67, 2.87, 2.70, 2.91, 3.18, 3.03],
    4: [1.96, 2.01, 2.28, 2.07, 1.88, 2.54, 2.21],
    10: [1.42, 1.38, 1.65, 1.70, 1.75, 1.59, 1.60],
    20: [1.18, 1.18, 1.16, 1.41, 1.51, 1.49, 1.51],
    100: [1.00, 1.00, 1.00, 1.00, 1.02, 1.08, 1.04]
}

colors = {2:'blue', 4:'green', 10:'orange', 20:'red', 100:'purple'}

plt.figure(figsize=(12, 6))

for d in reads:
    plt.plot(n_values, reads[d], marker='o', linestyle='-', color=colors[d], label=f'd={d} reads')
    plt.plot(n_values, writes[d], marker='x', linestyle='--', color=colors[d], label=f'd={d} writes')

plt.xscale('log')
plt.xlabel('n')
plt.ylabel('Average access count')
plt.title('Tree reads and writes for different d values (ADD test)')
plt.legend()
plt.grid(True, which="both", ls="--")
plt.show()

n = [20, 50, 100, 200, 500, 1000, 2000]

reads = {
    2:   [2.40, 3.64, 3.85, 4.76, 5.60, 5.50, 6.46],
    4:   [2.10, 2.28, 2.93, 3.48, 3.34, 4.14, 4.34],
    10:  [1.50, 1.96, 2.12, 2.38, 3.08, 3.12, 3.22],
    20:  [2.00, 1.68, 1.92, 2.24, 2.00, 2.02, 3.02],
    100: [2.00, 2.00, 2.00, 1.02, 2.02, 2.00, 2.02],
}

writes = {
    2:   [1.70, 2.50, 2.34, 2.12, 1.96, 1.82, 1.79],
    4:   [1.35, 1.50, 1.88, 1.75, 1.62, 1.32, 1.59],
    10:  [0.95, 1.18, 1.31, 1.59, 1.23, 1.23, 1.39],
    20:  [0.95, 1.08, 1.15, 1.37, 1.04, 1.06, 1.03],
    100: [0.95, 0.98, 0.99, 1.00, 1.04, 1.01, 1.03],
}

colors = {2:"blue", 4:"green", 10:"red", 20:"orange", 100:"purple"}

plt.figure(figsize=(10,6))

for d in reads:
    plt.plot(n, reads[d], marker="o", color=colors[d], label=f"reads d={d}")
    plt.plot(n, writes[d], marker="s", linestyle="--", color=colors[d], label=f"writes d={d}")

plt.xscale('log')
plt.xlabel('n')
plt.ylabel("Average access count")
plt.title("Tree reads and writes for different d values (DELETE test)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
