# Borderlands 2 Skin generator
At the moment, this project is a stub and barely functional.

# How to use:
 * Download and extract the repo somewhere.
 * Make sure you have the following python packages installed: [Cython](https://pypi.org/project/Cython/), [Pillow](https://pypi.org/project/Pillow/) and [numpy](https://pypi.org/project/numpy/).
   * You can do so with: `pip install -r requirements.txt`
 * Compile the .pyx files to binaries by running `setup.bat`. (For manual compiling check [Manually compiling cython modules](#manually-compiling-cython-modules).)
 * To extract the packets from Borderlands 2 use [UE Viewer/umodel](https://www.gildor.org/en/projects/umodel). The filepaths are hardcoded to locate the files the way UE Viewer extracts them.
 * Navigate a terminal to where you cloned the repository (The directory `skingen.py` is located in).
 * Run the program, for example: `python skingen.py -in C:\full\path\to\folder\CD_Assassin_Skin_OrangeD_SF`
   * This will save files in the current working directory, to specify another directory use the `-out <filepath>` command line argument.
   * For help on other options, run `python skingen.py` without any arguments.

If a result did not conform to your expectations (and it's damn likely it won't), feel free to open up an issue. Note that decals are a next point on the list, but I want to get the base functionality stable enough.

## Manually compiling cython modules
You will need [Cython](https://pypi.org/project/Cython/) to compile the .pyx files at `bl2_skingen/imaging` to binary files suited for your system.
Only `ue_color_diff.pyx` and `multiply_sqrt.pyx` are needed at the moment.
Navigate a terminal to the folder and run:
 * `python build_ue_color_diff.py build_ext --inplace`
 * `python build_multiply_sqrt.py build_ext --inplace`
