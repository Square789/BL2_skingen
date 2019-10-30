At the moment, this project is a stub and barely functional.

# Prerequisites:

You will need [pillow](https://pypi.org/project/Pillow/) and [numpy](https://pypi.org/project/numpy/).

You will need [Cython](https://pypi.org/project/Cython/) to compile the .pyx files at `bl2_skingen/imaging` to binary files suited for your system, as I have no idea how to automate that or to distribute the binaries.
Only `ue_color_diff.pyx` and `multiply_sqrt.pyx` are needed.
Navigate a terminal to the folder and run `py build_ue_color_diff.py build_ext --inplace` (and `build_multiply_sqrt.py` as well).

# How to use:
 * Download and extract the repo somewhere.
 * Use [UE Viewer/umodel](https://www.gildor.org/en/projects/umodel) to extract the packets from Borderlands, the filepaths are hardcoded to locate the files the way UE Viewer extracts them.
 * Navigate a terminal to the repo directory.
 * Run the program as follows: `py skingen.py -in C:\full\path\to\folder\CD_Assassin_Skin_OrangeD_SF`
  * This will save files in the current working directory, to specify another directory use the -out CL arg.

If a result did not conform to your expectations (and it's damn likely it won't), feel free to open up an issue. Note that decals are a next point on the list, but I want to get the base functionality stable enough.
