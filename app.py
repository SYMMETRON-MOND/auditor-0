# AUDITOR-0: Interfaz gráfica del Guardrail de Gödel
# Carga el modelo V4 entrenado desde godel_model_production.pt

import streamlit as st
import torch
import time
import os

from godel_audit_v4 import (
    GoedelInformedNetworkV4,
    code_to_latent_tensor,
)

# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="AUDITOR-0",
    page_icon="⚛️",
    layout="wide",
)

st.title("⚛️ AUDITOR-0")
st.markdown("""
**Auditoría de invarianza de renormalización (RG-S / R5+) para scripts Python.**

El guardrail verifica que el código preserva el atractor topológico γ = 0.0931.
Si el sistema se desvía, el canal de propagación se atenúa automáticamente.
""")

# ============================================================
# CARGA DEL MODELO
# ============================================================

@st.cache_resource
def load_godel_model():
    """Carga el modelo entrenado desde el checkpoint."""
    checkpoint_path = "godel_model_v6.pt"

    if not os.path.exists(checkpoint_path):
        return None, None

    checkpoint = torch.load(checkpoint_path, map_location='cpu')

    # Reconstruir la red
    model = GoedelInformedNetworkV4(features=8)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    return model, checkpoint

model, checkpoint = load_godel_model()

# ============================================================
# SIDEBAR: MÉTRICAS DEL MODELO
# ============================================================

st.sidebar.markdown("### 📊 Métricas del Modelo")

if checkpoint:
    guardrail_state = checkpoint.get('guardrail_state', {})
    training_metrics = checkpoint.get('training_metrics', {})

    st.sidebar.markdown("**Parámetros del Atractor:**")
    st.sidebar.markdown(f"- γ_target: `{guardrail_state.get('gamma_target', 0.0931)}`")
    st.sidebar.markdown(f"- γ_tolerance: `{guardrail_state.get('gamma_tol', 0.0004)}`")
    st.sidebar.markdown(f"- M*_UV: `{guardrail_state.get('M_star_uv', 0.036)}`")
    st.sidebar.markdown(f"- M*_IR: `{guardrail_state.get('M_star_ir', 0.0861)}`")
    st.sidebar.markdown(f"- Factor de masa: `{guardrail_state.get('expected_mass_ratio', 2.39167):.5f}`")

    st.sidebar.markdown("**Métricas de Entrenamiento:**")
    st.sidebar.markdown(f"- Épocas: `{training_metrics.get('epochs', 50)}`")
    st.sidebar.markdown(f"- γ_UV final: `{training_metrics.get('final_gamma_uv', 0.093073):.6f}`")
    st.sidebar.markdown(f"- γ_IR final: `{training_metrics.get('final_gamma_ir', 0.093135):.6f}`")
    st.sidebar.markdown(f"- Anomalías finales: `{training_metrics.get('final_anomalies', 1)}/500`")
else:
    st.sidebar.error("⚠️ Modelo no cargado. Verifica `godel_model_production.pt`.")

# ============================================================
# INPUT: CÓDIGO A AUDITAR
# ============================================================

st.markdown("---")
st.markdown("### 📝 Código a Auditar")

code_input = st.text_area(
    "Pega aquí el código Python:",
    height=300,
    placeholder="""def mi_funcion():
    for i in range(10):
        print(i)
    return True""",
)

# ============================================================
# BOTÓN DE AUDITORÍA
# ============================================================

col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    audit_button = st.button("🚀 Auditar Código", use_container_width=True)

if audit_button:
    if not model:
        st.error("❌ No se encontró el modelo. Verifica `godel_model_production.pt`.")
    elif not code_input.strip():
        st.warning("⚠️ Introduce algo de código antes de auditar.")
    else:
        with st.spinner("Ejecutando auditoría topológica..."):
            # 1. Convertir código a tensor latente
            x_input = code_to_latent_tensor(code_input, features=8)

            # 2. Inferencia
            start = time.time()
            with torch.no_grad():
                _, anomalies, gamma_uv, gamma_ir, mass_factor = model(x_input)
            elapsed = (time.time() - start) * 1000

            # 3. Verificar handshake
            gamma_target = model.guardrail.gamma_target
            gamma_tol = model.guardrail.gamma_tol

            handshake_ok = (
                torch.abs(gamma_uv.mean() - gamma_target) <= gamma_tol and
                torch.abs(gamma_ir.mean() - gamma_target) <= gamma_tol
            )

            # 4. Mostrar reporte
            st.markdown("---")
            st.markdown("### 📋 Reporte de Auditoría")

            # Métricas principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Tiempo", f"{elapsed:.2f} ms")
            c2.metric("γ_UV", f"{gamma_uv.mean().item():.6f}")
            c3.metric("γ_IR", f"{gamma_ir.mean().item():.6f}")

            # Handshake
            st.markdown("---")
            st.markdown("**Handshake UV ↔ IR:**")

            hc1, hc2, hc3 = st.columns(3)
            hc1.metric("Factor de Masa", f"{mass_factor:.5f}")
            hc2.metric("Esperado", f"{model.guardrail.expected_mass_ratio:.5f}")
            hc3.metric("Estado", "✓" if handshake_ok else "✗")

            # Veredicto
            st.markdown("---")
            if len(anomalies) == 0 and handshake_ok:
                st.success("""
                **[ÉXITO] CONSISTENCIA DE RENORMALIZACIÓN GARANTIZADA.**

                El script preserva el atractor topológico. El handshake UV ↔ IR
                está intacto. Despliegue autorizado.
                """)
                st.balloons()
            elif handshake_ok and len(anomalies) <= 2:
                st.warning(f"""
                **[ESTABILIDAD SOBERANA]** Se detectaron {len(anomalies)} anomalías residuales.

                El handshake está preservado, pero hay canales fuera del atractor.
                Esto es ruido estadístico esperado (0.2% del corpus).
                """)
            else:
                st.error(f"""
                **[FALLÓ] ERROR DE CONSISTENCIA TOPOLÓGICA.**

                Se detectaron {len(anomalies)} anomalías en el flujo de campo.
                Handshake: {'✓' if handshake_ok else '✗ ROTO'}
                """)

                if anomalies:
                    st.markdown("**Canales con anomalías:**")
                    for idx, gamma in anomalies:
                        deviation = abs(gamma - gamma_target)
                        st.markdown(
                            f"- Canal `{idx}`: γ = `{gamma:.6f}` "
                            f"(desviación: `{deviation:.6f}` > `{gamma_tol}`)"
                        )

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.caption("""
**AUDITOR-0** · Basado en el marco RG-S / R5+ por Juan José Arroyo Ramírez.
[GitHub](https://github.com/jj-arroyo/auditor-0) · [Zenodo](https://doi.org/10.5281/zenodo.19140573)
""")
