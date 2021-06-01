# Borderlands 2 Skin generator
Utility to generate png files from Borderlands 2 in-game skin files.

# How to use:
## Installation via PyPi
This project is available on [PyPi](https://pypi.org/project/BL2_skingen/), however pre-compiled binaries only come for Python 3.8 64bit on Windows.
If this meets your requirements, you can install it using `pip install BL2_skingen`, which will create the entry script `bl2-skingen`.

## Manual installation
 Should be handled by pip as long as you have a compiler and Cython set up, otherwise:
 * Download and extract the repo somewhere.
 * Make sure you have the following python packages installed: [Cython](https://pypi.org/project/Cython/), [Pillow](https://pypi.org/project/Pillow/) and [numpy](https://pypi.org/project/numpy/).
   * You can do so with: `pip install -r requirements.txt`
 * Navigate a terminal to the project's root folder.
 * Compile the .pyx files to binaries by running `py setup.py build_ext --inplace`.
## Usage
 * To extract the packets from Borderlands 2 use [UE Viewer/umodel](https://www.gildor.org/en/projects/umodel). The filepaths are hardcoded to locate the files the way UE Viewer extracts them.
  * If you installed the PyPi package, the entry script will be placed in `%PYTHONPATH%/Scripts` and should be accessible with `bl2-skingen` anywhere if the location is in your system's path.
  * If you installed the script manually, navigate a terminal to the directory, the script can be run there with `py <Installationdir>/skingen.py`
 * For help on options, run the script without any arguments.
 Example : `bl2-skingen C:\Skinfiles\CD_Assasin_OrangeD_SF -out C:\Skinfiles\GEN -exc-head`

If a result did not conform to your expectations (and it's likely it won't), feel free to open up an issue.
