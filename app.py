# app.py
# AUDITOR-0: Gödel Guardrail web interface

import streamlit as st
import torch
import time
import os

from godel_audit_v4 import (
    GoedelInformedNetworkV4,
    code_to_latent_tensor,
)


st.set_page_config(
    page_title="AUDITOR-0",
    page_icon="⚛️",
    layout="wide",
)

st.title("⚛️ AUDITOR-0")
st.markdown("""
**Renormalization invariance audit (RG-S / R5+) for Python scripts.**

The guardrail verifies that the code preserves the topological attractor γ = 0.0931.
""")


@st.cache_resource
def load_godel_model():
    checkpoint_path = "godel_model_v7.pt"
    if not os.path.exists(checkpoint_path):
        return None, None

    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    model = GoedelInformedNetworkV4(features=8)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    return model, checkpoint


model, checkpoint = load_godel_model()


st.sidebar.markdown("### 📊 Model Metrics")

if checkpoint:
    guardrail_state = checkpoint.get('guardrail_state', {})
    st.sidebar.markdown(f"- γ_target: `{guardrail_state.get('gamma_target', 0.0931)}`")
    st.sidebar.markdown(f"- γ_tolerance: `{guardrail_state.get('gamma_tol', 0.0004)}`")
    st.sidebar.markdown(f"- M*_UV: `{guardrail_state.get('M_star_uv', 0.036)}`")
    st.sidebar.markdown(f"- M*_IR: `{guardrail_state.get('M_star_ir', 0.0861)}`")
    st.sidebar.markdown(f"- Mass factor: `{guardrail_state.get('expected_mass_ratio', 2.39167):.5f}`")
else:
    st.sidebar.error("⚠️ Model not loaded. Check `godel_model_v7.pt`.")


st.markdown("---")
st.markdown("### 📝 Code to Audit")

code_input = st.text_area(
    "Paste your Python code here:",
    height=300,
    placeholder="def my_function():\n    for i in range(10):\n        print(i)\n    return True",
)


col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    audit_button = st.button("🚀 Audit Code", use_container_width=True)


if audit_button:
    if not model:
        st.error("❌ Model not found. Check `godel_model_v7.pt`.")
    elif not code_input.strip():
        st.warning("⚠️ Please paste some code before auditing.")
    else:
        with st.spinner("Running topological audit..."):
            x_input = code_to_latent_tensor(code_input, features=8)

            start = time.time()
            with torch.no_grad():
                _, anomalies, gamma_uv, gamma_ir, mass_factor = model(x_input)
            elapsed = (time.time() - start) * 1000

            gamma_target = model.guardrail.gamma_target
            gamma_tol = model.guardrail.gamma_tol
            handshake_ok = (
                torch.abs(gamma_uv.mean() - gamma_target) <= gamma_tol and
                torch.abs(gamma_ir.mean() - gamma_target) <= gamma_tol
            )

            st.markdown("---")
            st.markdown("### 📋 Audit Report")

            c1, c2, c3 = st.columns(3)
            c1.metric("Time", f"{elapsed:.2f} ms")
            c2.metric("γ_UV", f"{gamma_uv.mean().item():.6f}")
            c3.metric("γ_IR", f"{gamma_ir.mean().item():.6f}")

            st.markdown("**Handshake UV ↔ IR:**")
            hc1, hc2, hc3 = st.columns(3)
            hc1.metric("Mass Factor", f"{mass_factor:.5f}")
            hc2.metric("Expected", f"{model.guardrail.expected_mass_ratio:.5f}")
            hc3.metric("State", "✓" if handshake_ok else "✗")

            if len(anomalies) == 0 and handshake_ok:
                st.success("**[SUCCESS] RENORMALIZATION CONSISTENCY GUARANTEED.**")
                st.balloons()
            elif handshake_ok and len(anomalies) <= 2:
                st.warning(f"**[SOVEREIGN STABILITY]** {len(anomalies)} residual anomalies detected.")
            else:
                st.error(f"**[FAILED]** {len(anomalies)} anomalies detected.")
                for idx, gamma in anomalies:
                    st.markdown(f"- Channel {idx}: γ = `{gamma:.6f}`")


st.markdown("---")
st.caption("AUDITOR-0 · Based on the RG-S / R5+ framework by Juan José Arroyo Ramírez")
