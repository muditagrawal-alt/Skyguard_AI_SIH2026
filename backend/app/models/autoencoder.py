"""
SkyGuard AI - Temporal Sequence Autoencoder & Reconstruction Residual Network
Uses a PyTorch Autoencoder with local relative normalization to model temporal diurnal sequences
across Temperature, Pressure, and Humidity. Flags anomalies based on trajectory reconstruction error.
"""

import csv
from pathlib import Path

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Any, List, Optional

REAL_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "real_stations" / "processed"


class TemporalAutoencoderNN(nn.Module):
    def __init__(self, seq_len: int = 15, n_features: int = 3, latent_dim: int = 6):
        super(TemporalAutoencoderNN, self).__init__()
        self.seq_len = seq_len
        self.n_features = n_features
        input_dim = seq_len * n_features

        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.Tanh(),
            nn.Linear(32, 16),
            nn.Tanh(),
            nn.Linear(16, latent_dim)
        )

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 16),
            nn.Tanh(),
            nn.Linear(16, 32),
            nn.Tanh(),
            nn.Linear(32, input_dim)
        )

    def forward(self, x):
        z = self.encoder(x)
        reconstruction = self.decoder(z)
        return reconstruction


class TemporalAutoencoder:
    def __init__(self, seq_len: int = 15):
        self.seq_len = seq_len
        self.device = torch.device("cpu")
        self.model = TemporalAutoencoderNN(seq_len=seq_len).to(self.device)
        self.criterion = nn.MSELoss(reduction="none")
        self.is_trained = False
        self._quick_train_baseline()

    def _load_real_windows(self, max_windows: int = 600) -> Optional[np.ndarray]:
        """
        Builds locally-normalized [seq_len x 3] training windows from real NOAA
        ISD-Lite observations (see data/real_stations/), using the identical local
        mean/std normalization score_sequence() applies at inference time so the
        training distribution matches what the model actually sees in production.
        Windows spanning a timestamp gap > 4h (a dropped/missing real observation)
        are skipped so the model isn't taught that a big jump is a normal trajectory.
        Returns None if no processed real data is available.
        """
        if not REAL_DATA_DIR.is_dir():
            return None

        from datetime import datetime

        all_windows = []
        for csv_path in sorted(REAL_DATA_DIR.glob("*.csv")):
            with open(csv_path, newline="") as f:
                station_rows = list(csv.DictReader(f))
            if len(station_rows) < self.seq_len:
                continue

            times = [datetime.fromisoformat(r["timestamp"]) for r in station_rows]
            temps = [float(r["temperature_c"]) for r in station_rows]
            press = [float(r["pressure_hpa"]) for r in station_rows]
            hums = [float(r["humidity_pct"]) for r in station_rows]

            stride = 4  # overlapping windows every 4 hours keeps the dataset diverse but bounded
            for start in range(0, len(station_rows) - self.seq_len, stride):
                window_times = times[start:start + self.seq_len]
                gaps_hours = [
                    (window_times[i + 1] - window_times[i]).total_seconds() / 3600.0
                    for i in range(len(window_times) - 1)
                ]
                if max(gaps_hours) > 4.0:
                    continue
                window = np.array([
                    temps[start:start + self.seq_len],
                    press[start:start + self.seq_len],
                    hums[start:start + self.seq_len],
                ]).T
                all_windows.append(window)

        if not all_windows:
            return None

        rng = np.random.RandomState(42)
        if len(all_windows) > max_windows:
            idx = rng.choice(len(all_windows), size=max_windows, replace=False)
            all_windows = [all_windows[i] for i in idx]

        normalized = []
        for w in all_windows:
            means = np.mean(w, axis=0)
            stds = np.std(w, axis=0)
            stds = np.where(stds < 0.5, 1.0, stds)
            normalized.append(((w - means) / stds).flatten())

        return np.array(normalized, dtype=np.float32)

    def _quick_train_baseline(self):
        """
        Trains the autoencoder on smooth synthetic sinusoidal trajectories blended
        with locally-normalized windows drawn from real NOAA ISD-Lite station data
        (when available -- see data/real_stations/), so it masters both idealized
        diurnal cycles and genuine real-world meteorological trajectories.
        """
        torch.manual_seed(42)
        np.random.seed(42)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)

        batch_seqs = []
        for _ in range(500):
            t0 = np.random.uniform(0, 24)
            time_steps = np.linspace(t0, t0 + 1.5, self.seq_len)

            # Synthetic normalized smooth curves
            temp_seq = np.sin(2 * np.pi * time_steps / 24.0) + np.random.normal(0, 0.05, self.seq_len)
            hum_seq = -np.sin(2 * np.pi * time_steps / 24.0) + np.random.normal(0, 0.05, self.seq_len)
            pres_seq = np.sin(4 * np.pi * time_steps / 24.0) * 0.3 + np.random.normal(0, 0.05, self.seq_len)

            seq_matrix = np.column_stack([temp_seq, pres_seq, hum_seq]).flatten()
            batch_seqs.append(seq_matrix)

        real_windows = self._load_real_windows()
        if real_windows is not None:
            batch_seqs.extend(real_windows)
            self.real_data_windows = len(real_windows)
        else:
            self.real_data_windows = 0

        tensor_data = torch.tensor(np.array(batch_seqs), dtype=torch.float32)

        self.model.train()
        for epoch in range(60):
            optimizer.zero_grad()
            recon = self.model(tensor_data)
            loss = nn.MSELoss()(recon, tensor_data)
            loss.backward()
            optimizer.step()

        self.model.eval()
        self.is_trained = True

    def score_sequence(self, sequence_window: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Receives the last `seq_len` readings: [{temp, pres, hum}, ...]
        Performs local relative normalization to evaluate trajectory smoothness.
        """
        if len(sequence_window) < self.seq_len:
            pad_needed = self.seq_len - len(sequence_window)
            first_item = sequence_window[0] if sequence_window else {"temperature": 25.0, "pressure": 1000.0, "humidity": 60.0}
            padded_window = [first_item] * pad_needed + list(sequence_window)
        else:
            padded_window = list(sequence_window[-self.seq_len:])

        raw_array = np.array([
            [r.get("temperature", 25.0) or 25.0, 
             r.get("pressure", 1000.0) or 1000.0, 
             r.get("humidity", 60.0) or 60.0]
            for r in padded_window
        ], dtype=np.float32)

        # Local relative standardization per sequence
        means = np.mean(raw_array, axis=0)
        stds = np.std(raw_array, axis=0)
        stds = np.where(stds < 0.5, 1.0, stds)  # Prevent divide-by-zero on flat periods

        norm_array = (raw_array - means) / stds
        flat_input = norm_array.flatten()
        tensor_in = torch.tensor(flat_input, dtype=torch.float32).unsqueeze(0).to(self.device)

        with torch.no_grad():
            tensor_recon = self.model(tensor_in)
            mse_per_element = self.criterion(tensor_recon, tensor_in).squeeze(0).numpy()
            
        element_errors = mse_per_element.reshape(self.seq_len, 3)
        # Recent timesteps weighted higher
        recent_err = np.mean(element_errors[-3:, :])

        # Smooth baseline sequences produce recent_err < 0.35
        # Sudden shocks produce recent_err > 1.2
        ae_anomaly_prob = min(1.0, max(0.0, (recent_err - 0.25) / 1.5))

        return {
            "reconstruction_mse": round(float(recent_err), 4),
            "ae_anomaly_prob": round(float(ae_anomaly_prob), 4),
            "recent_temp_err": round(float(element_errors[-1, 0]), 4),
            "recent_pres_err": round(float(element_errors[-1, 1]), 4),
            "recent_hum_err": round(float(element_errors[-1, 2]), 4)
        }


temporal_autoencoder = TemporalAutoencoder(seq_len=15)
