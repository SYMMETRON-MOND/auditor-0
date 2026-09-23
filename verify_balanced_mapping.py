# Verifica que el mapeo balanceado discrimina los tres casos

import math
import torch
from godel_audit_v4 import code_to_latent_tensor


# ============================================================
# LOS TRES SCRIPTS DE PRUEBA
# ============================================================

script_a = """def suma(a, b):
    return a + b
"""

script_b = """def process_data(data):
    try:
        result = []
        for item in data:
            if item > 0:
                result.append(item * 2)
            elif item < 0:
                result.append(item / 2)
            else:
                result.append(0)
        return result
    except Exception:
        return None
"""

script_c = """while True:
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
    except:
        catch
"""


# ============================================================
# MAPEO
# ============================================================

tensor_a = code_to_latent_tensor(script_a)
tensor_b = code_to_latent_tensor(script_b)
tensor_c = code_to_latent_tensor(script_c)


# ============================================================
# REPORTE
# ============================================================

print("=" * 70)
print("VERIFICACIÓN DEL MAPEO BALANCEADO")
print("=" * 70)

print("\nScript A (trivial):")
print(tensor_a.numpy().flatten())

print("\nScript B (moderado):")
print(tensor_b.numpy().flatten())

print("\nScript C (caótico):")
print(tensor_c.numpy().flatten())

print("\n" + "=" * 70)
print("DISTANCIAS EUCLIDIANAS:")
print("=" * 70)

d_ab = torch.norm(tensor_a - tensor_b).item()
d_bc = torch.norm(tensor_b - tensor_c).item()
d_ac = torch.norm(tensor_a - tensor_c).item()

print(f"d(A, B) = {d_ab:.4f}")
print(f"d(B, C) = {d_bc:.4f}")
print(f"d(A, C) = {d_ac:.4f}")

print("\n" + "=" * 70)
print("VEREDICTO:")
print("=" * 70)

if d_ab > 1.0 and d_bc > 1.0 and d_ac > 1.0:
    print("✅ EL MAPEO DISCRIMINA.")
    print("   Los tres scripts producen tensores distintos.")
    print("   Procede a reentrenar el modelo.")
elif d_ab > 0.5 and d_bc > 0.5 and d_ac > 0.5:
    print("⚠️ EL MAPEO DISCRIMINA PARCIALMENTE.")
    print("   Considera amplificar los coeficientes.")
else:
    print("❌ EL MAPEO NO DISCRIMINA.")
    print("   Aumenta los coeficientes del mapeo.")
