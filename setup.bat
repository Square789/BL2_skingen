@echo off
cd bl2_skingen/imaging
py build.py build_ext --inplace --build_needed_only
cd ../..
pause
