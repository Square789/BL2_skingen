cd bl2_skingen/imaging
py build_ue_color_diff.py build_ext --inplace
py build_multiply_sqrt.py build_ext --inplace
::py build_darken.py build_ext --inplace
::py build_overlay.py build_ext --inplace
cd ../..
pause