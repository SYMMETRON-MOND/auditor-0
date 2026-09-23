import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

from godel_audit_v4 import GoedelInformedNetworkV4, code_to_latent_tensor

torch.manual_seed(42)
np.random.seed(42)


def generate_script(rng):
    complexity = rng.integers(0, 4)
    if complexity == 0:
        return "def f():\n    return 1\n"
    elif complexity == 1:
        return "def f(x):\n    for i in range(x):\n        pass\n    return x\n"
    elif complexity == 2:
        return """
def process(data):
    try:
        result = []
        for item in data:
            if item > 0:
                result.append(item * 2)
        return result
    except:
        return None
"""
    else:
        return """
while True:
    try:
        for i in range(1000):
            for j in range(1000):
                for k in range(1000):
                    if i > j:
                        if j > k:
                            if k > 0:
                                pass
    except:
        pass
"""


rng = np.random.default_rng(42)
N_SAMPLES = 500

scripts = [generate_script(rng) for _ in range(N_SAMPLES)]
X_train = torch.cat([code_to_latent_tensor(s, features=8) for s in scripts], dim=0)
y_train = torch.randn(N_SAMPLES, 1)

model = GoedelInformedNetworkV4(features=8)
optimizer = optim.Adam(model.parameters(), lr=0.001)
criterion = nn.MSELoss()

EPOCHS = 50
LAMBDA_GODEL = 1.0
BATCH_SIZE = 32

print("=" * 72)
print("     REENTRENAMIENTO CON MAPEO BALANCEADO (v6)")
print("=" * 72)

for epoch in range(EPOCHS):
    model.train()
    epoch_mse = 0.0
    epoch_godel = 0.0
    epoch_anomalies = 0
    n_batches = 0

    indices = torch.randperm(N_SAMPLES)
    for i in range(0, N_SAMPLES, BATCH_SIZE):
        batch_idx = indices[i:i+BATCH_SIZE]
        batch_x = X_train[batch_idx]
        batch_y = y_train[batch_idx]

        optimizer.zero_grad()
        out, anomalies, gamma_uv, gamma_ir, _ = model(batch_x)

        mse_loss = criterion(out, batch_y)
        godel_loss = torch.mean(torch.abs(gamma_ir - model.guardrail.gamma_target))
        total_loss = mse_loss + LAMBDA_GODEL * godel_loss

        total_loss.backward()
        optimizer.step()

        epoch_mse += mse_loss.item()
        epoch_godel += godel_loss.item()
        epoch_anomalies += len(anomalies)
        n_batches += 1

    if (epoch + 1) % 5 == 0 or epoch == 0:
        print(f"[{epoch+1:02d}/{EPOCHS}] MSE: {epoch_mse/n_batches:.4f} | Gödel: {epoch_godel/n_batches:.8f} | Anomalías: {epoch_anomalies}")

print("-" * 72)
print("Reentrenamiento completado.")

torch.save({
    'model_state_dict': model.state_dict(),
    'guardrail_state': {
        'gamma_target': model.guardrail.gamma_target,
        'gamma_tol': model.guardrail.gamma_tol,
        'M_star_uv': model.guardrail.M_star_uv,
        'M_star_ir': model.guardrail.M_star_ir,
    },
    'version': 'v6',
    'mapping': 'balanced',
}, "godel_model_v6.pt")

print("Modelo v6 guardado.")
