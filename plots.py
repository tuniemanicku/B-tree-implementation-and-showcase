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
    # Measured data
    ax.plot(n, values, marker="o", label="Measured")

    # ceil(log_d(n))
    log_vals = [math.ceil(math.log(ni, d)) for ni in n]
    ax.plot(n, log_vals, linestyle="--", marker="s", label=r"$\lceil \log_d(n) \rceil$")

    ax.set_xscale("log")
    ax.set_ylabel("Value")
    ax.set_title(f"d = {d}")
    ax.grid(True, which="both", linestyle="--", alpha=0.6)
    ax.legend()

axes[-1].set_xlabel("n")
plt.tight_layout()
plt.show()