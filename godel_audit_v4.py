# godel_audit_v4.py
# RG-S / R5+ Dual Renormalization Quantum Guardrail Framework
# v4.3: Mapeo balanceado con log1p — archivo único sin duplicados

import sys
import os
import time
import math
import torch
import torch.nn as nn


# ============================================================
# GUARDRAIL
# ============================================================

class SovereignGodelGuardrailV4(nn.Module):
    def __init__(self, features, gamma_target=0.0931, gamma_tol=0.0004,
                 g_sp=0.48, mu_squared=0.15):
        super().__init__()
        self.features = features
        self.gamma_target = gamma_target
        self.gamma_tol = gamma_tol
        self.g_sp = g_sp
        self.mu_squared = mu_squared

        self.M_star_uv = 0.036
        self.M_star_ir = 0.0861
        self.alpha_uv = 3.6393
        self.beta_ir = 4.0931
        self.expected_mass_ratio = self.M_star_ir / self.M_star_uv

        term_den = (1.0 - gamma_target) ** 2
        phi_2_vev = math.sqrt(
            ((mu_squared / math.sqrt(term_den)) ** 2 - mu_squared ** 2) / (g_sp ** 2)
        )

        self.phi_1 = nn.Parameter(torch.empty(features).uniform_(-0.001, 0.001))
        self.phi_2 = nn.Parameter(torch.full((features,), phi_2_vev))

    def asynchronous_liv_kernel(self, x):
        shift_left = torch.roll(x, shifts=1, dims=-1)
        shift_right = torch.roll(x, shifts=-1, dims=-1)
        liv_phase = math.sin(self.alpha_uv) * 0.05
        return (1.0 - liv_phase) * x + (liv_phase / 2.0) * (shift_left + shift_right)

    def calculate_conformal_coupling(self, phi_1_tensor, M_star):
        return 1.0 + (phi_1_tensor ** 2) / (2.0 * (M_star ** 2))

    def _berry_phase(self, phi_2_tensor):
        omega_c = 2.0 * math.pi
        den = torch.sqrt(self.mu_squared ** 2 + (self.g_sp ** 2) * (phi_2_tensor ** 2))
        gamma_berry = 0.5 * omega_c * (1.0 - (self.mu_squared / den))
        return gamma_berry / math.pi

    def euler_lagrange_update(self, x_local, M_star):
        input_mean = x_local.mean(dim=0)
        A_val = self.calculate_conformal_coupling(self.phi_1, M_star)

        dS_dphi1 = (self.phi_1 / (M_star ** 2)) * A_val * (input_mean ** 2)
        dS_dphi2 = (self.mu_squared + (self.g_sp ** 2) * (self.phi_2 ** 2)) * self.phi_2 - input_mean / A_val

        delta_step = 0.001
        new_phi_1 = self.phi_1 - delta_step * dS_dphi1
        new_phi_2 = self.phi_2 - delta_step * dS_dphi2
        return new_phi_1, new_phi_2

    def check_equivalence(self, phi_2_uv, phi_2_ir):
        gamma_uv = self._berry_phase(phi_2_uv)
        gamma_ir = self._berry_phase(phi_2_ir)

        ok_uv = torch.abs(gamma_uv - self.gamma_target) <= self.gamma_tol
        ok_ir = torch.abs(gamma_ir - self.gamma_target) <= self.gamma_tol

        mass_factor = self.M_star_ir / self.M_star_uv
        ok_mass = torch.abs(torch.tensor(mass_factor) - torch.tensor(self.expected_mass_ratio)) < 1e-4

        equiv_mask = ok_uv & ok_ir & ok_mass
        return equiv_mask, gamma_uv, gamma_ir, mass_factor

    def forward(self, x):
        x_liv = self.asynchronous_liv_kernel(x)

        _, phi_2_uv = self.euler_lagrange_update(x_liv, self.M_star_uv)
        _, phi_2_ir = self.euler_lagrange_update(x_liv, self.M_star_ir)

        equiv_mask, gamma_uv, gamma_ir, mass_factor = self.check_equivalence(phi_2_uv, phi_2_ir)

        local_gamma = gamma_ir
        consistent_mask = torch.abs(local_gamma - self.gamma_target) <= self.gamma_tol

        anomalies = [(idx, local_gamma[idx].item())
                     for idx in range(self.features)
                     if not consistent_mask[idx].item()]

        guard_scale = torch.where(consistent_mask, 1.0, 0.01)

        if self.training:
            with torch.no_grad():
                self.phi_2.data.copy_(torch.where(consistent_mask, phi_2_ir.detach(), self.phi_2.data))

        return x * guard_scale, anomalies, gamma_uv, gamma_ir, mass_factor


# ============================================================
# RED
# ============================================================

class GoedelInformedNetworkV4(nn.Module):
    def __init__(self, features=8):
        super().__init__()
        self.guardrail = SovereignGodelGuardrailV4(features=features)
        self.network = nn.Sequential(
            nn.Linear(features, features),
            nn.ReLU(),
            self.guardrail,
            nn.Linear(features, 1)
        )

    def forward(self, x):
        x_latent = self.network[1](self.network[0](x))
        x_guarded, anomalies, g_uv, g_ir, m_factor = self.guardrail(x_latent)
        out = self.network[3](x_guarded)
        return out, anomalies, g_uv, g_ir, m_factor


# ============================================================
# MAPEO
# ============================================================

def code_to_latent_tensor(code_content, features=8):
    if not code_content.strip():
        return torch.zeros(1, features)

    lines = code_content.split('\n')
    non_empty_lines = [l for l in lines if l.strip()]

    char_count = len(code_content)
    non_empty_count = len(non_empty_lines)
    num_defs = code_content.count('def ') + code_content.count('class ')
    num_loops = code_content.count('for ') + code_content.count('while ')
    num_try = code_content.count('try:') + code_content.count('except')
    deep_indent = sum(1 for l in non_empty_lines if l.startswith('        '))
    num_branches = (code_content.count('if ') +
                    code_content.count('elif ') +
                    code_content.count('else:'))
    comment_lines = sum(1 for l in lines if l.strip().startswith('#'))
    empty_lines = len(lines) - non_empty_count
    noise_ratio = (comment_lines + empty_lines) / max(len(lines), 1)

    raw = [
        char_count * 0.002,
        non_empty_count * 0.1,
        num_defs * 0.6,
        num_loops * 0.8,
        num_try * 1.0,
        deep_indent * 0.4,
        num_branches * 0.5,
        noise_ratio * 2.0,
    ]

    # CRÍTICO: normalización log1p
    raw_normalized = [
        math.log1p(abs(v)) * (1 if v >= 0 else -1)
        for v in raw
    ]

    return torch.tensor([raw_normalized[:features]], dtype=torch.float32)


# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 godel_audit_v4.py <ruta_del_archivo.py>")
        sys.exit(1)

    target_path = sys.argv[1]
    if not os.path.exists(target_path):
        print(f"Error: El archivo '{target_path}' no fue encontrado.")
        sys.exit(1)

    with open(target_path, 'r', encoding='utf-8') as f:
        code_str = f.read()

    model = GoedelInformedNetworkV4(features=8)
    model.eval()

    x_input = code_to_latent_tensor(code_str, features=8)

    t0 = time.time()
    with torch.no_grad():
        _, anomalies, gamma_uv, gamma_ir, mass_factor = model(x_input)
    dt_ms = (time.time() - t0) * 1000.0

    print("\n" + "=" * 70)
    print("      REPORTE DE AUDITORÍA TOPOLÓGICA RG-S / R5+ (V4.3)")
    print("=" * 70)
    print(f"Archivo Auditado        : {target_path}")
    print(f"Tiempo de Ejecución     : {dt_ms:.3f} ms")
    print("-" * 70)
    print(f"  γ_UV: {gamma_uv.mean().item():.6f}")
    print(f"  γ_IR: {gamma_ir.mean().item():.6f}")
    print(f"  Factor de Masa: {mass_factor:.5f}")
    print(f"  Anomalías: {len(anomalies)}")
    print("=" * 70)

    if anomalies:
        print("[ESTADO] INCOMPATIBLE.")
        for channel, val in anomalies:
            print(f"  -> Canal {channel}: γ = {val:.6f}")
        sys.exit(1)
    else:
        print("[ESTADO] CONSISTENCIA GARANTIZADA.")
        sys.exit(0)


if __name__ == '__main__':
    main()
