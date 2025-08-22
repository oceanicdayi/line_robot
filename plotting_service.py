# plotting_service.py
import os
import uuid
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # 使用非互動式後端
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import matplotlib.cm as cm
from config import STATIC_DIR, CURRENT_YEAR

# Note: The setup_chinese_font function is no longer needed as all text will be in English.

def create_and_save_map(df: pd.DataFrame) -> str:
    """Create an earthquake map, save the image, and return the filename."""
    # The call to setup_chinese_font() has been removed.
    fig, ax = plt.subplots(figsize=(9, 6), dpi=150)
    ax.set_xlim(118.5, 123.5)
    ax.set_ylim(20.5, 26.8)
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    
    # [MODIFIED] The title has been changed to English.
    ax.set_title(f"Significant Earthquakes (M≥5.0) in Taiwan Area This Year ({CURRENT_YEAR}) — UTC")
    
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.4)

    mags = df["magnitude"].astype(float).clip(lower=0)
    norm = Normalize(vmin=max(4.5, mags.min()), vmax=max(6.5, mags.max()))
    cmap = cm.get_cmap("YlOrRd")
    colors = cmap(norm(mags.values))
    sizes = 15 + (mags - mags.min()) * 25

    ax.scatter(df["longitude"].values, df["latitude"].values,
               s=sizes, c=colors, edgecolor="k", linewidths=0.4, alpha=0.9)

    fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, pad=0.02).set_label("Magnitude")

    filename = f"map_{uuid.uuid4().hex}.png"
    filepath = os.path.join(STATIC_DIR, filename)
    fig.tight_layout()
    fig.savefig(filepath)
    plt.close(fig)
    return filename
