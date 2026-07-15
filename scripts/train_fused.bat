@echo off
REM ============================================================================
REM  train_fused.bat  --  collect -> prepare -> train the fused mind (Path B).
REM
REM  The fused mind conditions a transformer on the whole cognitive cycle as a
REM  numeric vector m_t (ADR 0005). This script runs the entire pipeline:
REM    1. collect fresh traces that carry m_t (state_vec)
REM    2. build the fused dataset (keeps m_t per example)
REM    3. train LoRA + the state encoder end-to-end (6 GB-tuned)
REM
REM  Run it from the repo root with your training venv active, e.g.:
REM      .venv312\Scripts\activate.bat
REM      scripts\train_fused.bat
REM  (double-clicking works too — it finds the repo root itself).
REM ============================================================================

setlocal ENABLEDELAYEDEXPANSION

REM --- knobs (edit these if you like) ----------------------------------------
REM   BACKEND : voice used while collecting traces (ollama | simulated | llm)
if "%BACKEND%"==""  set "BACKEND=ollama"
if "%TRACES%"==""   set "TRACES=data\traces_fused.jsonl"
if "%OUTDIR%"==""   set "OUTDIR=data\fused"
if "%MODEL%"==""    set "MODEL=models\sentiance-fused"
if "%EPOCHS%"==""   set "EPOCHS=4"
if "%NPREFIX%"==""  set "NPREFIX=8"

REM --- go to the repo root (this script lives in scripts\) --------------------
cd /d "%~dp0.."

REM --- activate the training venv if present and not already active ----------
if not defined VIRTUAL_ENV (
  if exist ".venv312\Scripts\activate.bat" call ".venv312\Scripts\activate.bat"
)
if not defined VIRTUAL_ENV (
  if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
)

echo(
echo === Fused mind training pipeline ===
echo   collection voice : %BACKEND%
echo   traces file      : %TRACES%
echo   dataset out      : %OUTDIR%
echo   model out        : %MODEL%   (epochs %EPOCHS%, n_prefix %NPREFIX%)
echo(

set "SENTIANCE_COGNITION_BACKEND=%BACKEND%"
set "SENTIANCE_TRACE_PATH=%TRACES%"

REM ---------------------------------------------------------------------------
echo [1/4] Collecting fresh traces (each run appends to %TRACES%)...
echo(
python -m sentiance society --trace
python -m sentiance society --trace
python -m sentiance live --as Iris --trace
python -m sentiance live --as Milo --trace
python -m sentiance live --as Cass --trace
python -m sentiance chat --preset --as Rhea --trace

REM ---------------------------------------------------------------------------
echo(
echo [2/4] Checking the traces carry m_t (state_vec)...
python -c "import json;r=[json.loads(l) for l in open(r'%TRACES%',encoding='utf-8') if l.strip()];n=sum('state_vec' in x for x in r);print('  rows',len(r),' with state_vec',n);import sys;sys.exit(0 if n>0 else 1)"
if errorlevel 1 (
  echo(
  echo   ERROR: no traces have state_vec. Are you on the latest code?
  echo          Run:  git pull origin claude/sentiance-repo-wa23as
  goto :fail
)

REM ---------------------------------------------------------------------------
echo(
echo [3/4] Building the fused dataset (keeps m_t per example)...
python scripts\prepare_data.py --traces "%TRACES%" --out "%OUTDIR%" --fused
if errorlevel 1 goto :fail
if not exist "%OUTDIR%\train.jsonl" (
  echo   ERROR: %OUTDIR%\train.jsonl was not written.
  goto :fail
)

REM ---------------------------------------------------------------------------
echo(
echo [4/4] Training the fused mind (LoRA + state encoder, end-to-end)...
echo       ^(look for "device: cuda" below; on CPU this is very slow^)
echo(
python scripts\finetune_fused.py --train "%OUTDIR%\train.jsonl" --out "%MODEL%" --epochs %EPOCHS% --n-prefix %NPREFIX%
if errorlevel 1 goto :fail

echo(
echo === Done. The fused mind is saved to %MODEL% ===
echo Use it:
echo     set SENTIANCE_COGNITION_BACKEND=fused
echo     python -m sentiance chat
echo(
goto :end

:fail
echo(
echo *** Pipeline stopped on an error (see the message above). ***
exit /b 1

:end
endlocal
