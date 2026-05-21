#!/usr/bin/env bash

set -e

BASE="releases/2026.04/evidence"

# --------------------------------------------------
# Create evidence directory structure
# --------------------------------------------------

mkdir -p "$BASE/RLSE1000001"
mkdir -p "$BASE/RLSE1000002"
mkdir -p "$BASE/Dynamic Scheduling and Schedule Optimisation"

# --------------------------------------------------
# RLSE1000001
# --------------------------------------------------

touch "$BASE/RLSE1000001/EX01.png"
touch "$BASE/RLSE1000001/EX02.png"
touch "$BASE/RLSE1000001/EX03.png"

touch "$BASE/RLSE1000001/EX10.png"
touch "$BASE/RLSE1000001/EX11.png"
touch "$BASE/RLSE1000001/EX12.png"

touch "$BASE/RLSE1000001/EX20.png"
touch "$BASE/RLSE1000001/EX21.png"

# --------------------------------------------------
# RLSE1000002
# --------------------------------------------------

touch "$BASE/RLSE1000002/AU01.png"
touch "$BASE/RLSE1000002/AU02.png"
touch "$BASE/RLSE1000002/AU03.png"
touch "$BASE/RLSE1000002/AU04.png"
touch "$BASE/RLSE1000002/AU05.png"

touch "$BASE/RLSE1000002/AU10.png"
touch "$BASE/RLSE1000002/AU11.png"
touch "$BASE/RLSE1000002/AU12.png"

touch "$BASE/RLSE1000002/AU20.png"
touch "$BASE/RLSE1000002/AU21.png"

touch "$BASE/RLSE1000002/AU30.png"
touch "$BASE/RLSE1000002/AU30_dup.png"

touch "$BASE/RLSE1000002/AU31.png"

touch "$BASE/RLSE1000002/AU41.docx"

# --------------------------------------------------
# Dynamic Scheduling and Schedule Optimisation
# --------------------------------------------------

touch "$BASE/Dynamic Scheduling and Schedule Optimisation/TP-CREW-01.docx"
touch "$BASE/Dynamic Scheduling and Schedule Optimisation/TP-CREW-02.docx"
touch "$BASE/Dynamic Scheduling and Schedule Optimisation/TP-CREW-03.docx"

touch "$BASE/Dynamic Scheduling and Schedule Optimisation/TP-OPT-01.docx"
touch "$BASE/Dynamic Scheduling and Schedule Optimisation/TP-OPT-02.docx"
touch "$BASE/Dynamic Scheduling and Schedule Optimisation/TP-OPT-03.docx"

touch "$BASE/Dynamic Scheduling and Schedule Optimisation/TP-MIS-01.docx"

# --------------------------------------------------
# Evidence range expansion
# --------------------------------------------------

touch "$BASE/Dynamic Scheduling and Schedule Optimisation/IS70A-D.docx"

echo "Synthetic regression evidence created."

