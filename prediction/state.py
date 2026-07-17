from __future__ import annotations

import pandas as pd

# ==========================================================
# KONSTANTA
# ==========================================================

WINDOW_SIZE = 8

DEFAULT_WIND = 25.0
DEFAULT_PRESS = 1005.0


# ==========================================================
# DATAFRAME DEFAULT
# ==========================================================

def create_empty_dataframe() -> pd.DataFrame:
    """
    Membuat dataframe kosong untuk input observasi.
    """

    return pd.DataFrame(
        {
            "LAT": [0.0] * WINDOW_SIZE,
            "LON": [0.0] * WINDOW_SIZE,
            "WMO_WIND": [DEFAULT_WIND] * WINDOW_SIZE,
            "WMO_PRES": [DEFAULT_PRESS] * WINDOW_SIZE,
        }
    )


# ==========================================================
# INITIALIZE SESSION STATE
# ==========================================================

def initialize_state(st):

    if "draft_data" not in st.session_state:

        st.session_state.draft_data = (
            create_empty_dataframe()
        )

    if "prediction_input" not in st.session_state:

        st.session_state.prediction_input = None

    if "prediction_result" not in st.session_state:

        st.session_state.prediction_result = None

    if "editor_version" not in st.session_state:

        st.session_state.editor_version = 0


# ==========================================================
# RESET
# ==========================================================

def clear_prediction(st):

    st.session_state.draft_data = (
        create_empty_dataframe()
    )

    st.session_state.prediction_input = None

    st.session_state.prediction_result = None

    st.session_state.editor_version += 1
