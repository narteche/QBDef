# QBDef: A QBF Family Definition Processor and Generator
A tool to write QBF family defintions and obtain instances in QCIR or QDIMACS.

# Description
QBDef is a computer-tool written in Python designed to make the generation of QBF instances easier. The tool gets as input the formal defintion of a formula family in terms of some parameters and returns instances of it for specific values in the QCIR or QDIMACS formats.

# How to use it
The tool is written in Python, so it should work on every operating system. However, if you are using Windows, we recommend to run the tool using the Windows Subsystem for Liunx (WSL).

The tool requires:

1. Python parsing library [lark](https://github.com/lark-parser/lark): `$ pip install lark-parser`
2. Python 2 (the tool runs on Python 3 but Python 2 is needed to run some third-party code; make sure you have it installed, as, for instance, Ubuntu 20.04 no longer has it by default).
3. William Klieber's `qcir-to-qdimacs.py` conversion tool. A copy of his script is available [in this same repo](https://github.com/alephnoell/QBDeF/blob/master/qcir-to-qdimacs.py). The orignal source is [this](https://www.wklieber.com/ghostq/qcir-converter.html). The script must be in the same directory as the tool to be able to output QDIMACS files.

You can run the tool by executing the [`QBDef.pyc`](https://github.com/alephnoell/QBDeF/blob/master/QBDeF.py) script on a terminal:

```
python QBDeF.pyc input_file [-internal] [-verbose] [-QDIMACS {file.qdimacs | [-stdIO]}] [-QCIR {file.QCIR | [-stdIO]}] [-non-prenex-QCIR {file.QCIR | [-stdIO]}]
```

For example, if `my_def.txt` is your QBF family definition and `values.txt` is the file with the values for the parameters,

```
python QBDeF.pyc my_def.txt values.txt -QCIR
```

outputs the QCIR format instance on terminal. 

The possible options are:

* `-QCIR    [output_file]`: outputs a QCIR, if no output file is provided, it is printed in the standard output.
* `-QDIMACS [output_file]`: outputs a QDIMACS, if no output file is provided, it is printed in the standard output.
* `-non-prenex-QCIR [output_file]`: outputs a non-prenex QCIR. This feature is experimental.
* `-internal`             : outputs a human-readable version of the internal representation of the QBF.
* `-verbose`              : prints messages while parsing and processing the definition.

# The formal language

Formula family defintions are written in a formal language parsed by the generator, which then outputs an actual instance in a valid format for some values of the family's parameters. The `/examples` folder contains examples of formula families written in the formal language. A cheatsheet is also provided in the same forlder.

# Contents of the repository

* `QBDef.pyc`: Python script to run the tool.
* `/examples`: definitions in the formal language; contains a brief introductory cheatsheet to the formal language.
* `/src`: source code and development files.

