"""UI palette (redesign). Colours only - no logic.

Old names (NAVY, GREEN, ...) are kept as aliases so chart code stays readable.
"""
SIDEBAR = "#252535"   # dark navy
TEAL = "#6FAFA5"      # primary accent
SAGE = "#A8DCA6"      # secondary accent
CORAL = "#FF876F"     # highlight
INK = "#30303A"       # main text
MUTED = "#7B7F8C"     # secondary text
GRID = "#E8EEEC"
BG = "#F3F8F6"
CARD = "#FFFFFF"

NAVY, GREEN, SLATE, SAND = SIDEBAR, TEAL, "#8C8CA6", "#E7C77F"

CATEGORY_COLORS = [TEAL, SIDEBAR, CORAL, SAGE, SLATE, SAND]
# The same three period colours are used on every page.
PERIOD_COLORS = {"Pre-Pandemic": SAGE, "Pandemic": CORAL, "Post-Pandemic": TEAL}
MODEL_COLORS = {"Seasonal Naive": SLATE, "SARIMA": TEAL}
