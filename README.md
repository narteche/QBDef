# QBDef: A QBF Family Definition Processor and Generator
A tool to write QBF family definitions and obtain instances in QCIR or QDIMACS.

# Description
QBDef is a computer-tool written in Python designed to make the generation of QBF instances easier. The tool gets as input the formal definition of a formula family in terms of some parameters and returns instances of it for specific values in the QCIR or QDIMACS formats.

# Requirements
The tool is written in Python, so it should work on any operating system. However, if you are using Windows, we recommend running the tool using the Windows Subsystem for Linux (WSL).

The tool requires:

1. Python parsing library [lark](https://github.com/lark-parser/lark): `pip install lark-parser`
2. Python 2 (the tool runs on Python 3 but Python 2 is needed to run some third-party code; make sure you have it installed, as, for instance, Ubuntu 20.04 no longer has it by default). Check that you have both with `python2 --version` and `python3 --version`.
3. William Klieber's `qcir-to-qdimacs.py` conversion tool. A copy of his script is available [in this same repo](https://github.com/alephnoell/QBDef/blob/master/qcir-to-qdimacs.py). The original source is [this](https://www.wklieber.com/ghostq/qcir-converter.html). The script must be in the same directory as the tool to be able to output QDIMACS files. This is already in the directory if you clone the repository.

# How to run QBDef
After cloning the repository, you can run the tool by executing the [`QBDef.py`](https://github.com/alephnoell/QBDef/blob/master/QBDef.py) script on a terminal:

```
python3 QBDef.py definition_file values_file [-internal] [-verbose] [-QDIMACS {file.qdimacs | [-stdIO]}] [-QCIR {file.QCIR | [-stdIO]}] [-non-prenex-QCIR {file.QCIR | [-stdIO]}]
```

For example, if `my_def.txt` is your QBF family definition and `values.txt` is the file with the values for the parameters,

```
python3 QBDef.py my_def.txt values.txt -QCIR
```

outputs the QCIR format instance on a terminal. 

The possible options are:

* `-QCIR    [output_file]`: outputs a QCIR, if no output file is provided, it is printed in the standard output.
* `-QDIMACS [output_file]`: outputs a QDIMACS, if no output file is provided, it is printed in the standard output.
* `-non-prenex-QCIR [output_file]`: outputs a non-prenex QCIR. This feature is experimental.
* `-internal`             : outputs a human-readable version of the internal representation of the QBF.
* `-verbose`              : prints messages while parsing and processing the definition.

# The formal language

Formula family definitions are written in a formal language parsed by the generator, which then outputs an actual instance in a valid format for some values of the family's parameters. [The cheat sheet](https://github.com/alephnoell/QBDef/blob/master/QBDef%20Cheatsheet.pdf) contains information on the syntax and format of this language. The [`/examples`](https://github.com/alephnoell/QBDef/tree/master/examples) folder contains examples of formula families written in the formal language. An interesting and simple example is that of [the QParity formulas](https://github.com/alephnoell/QBDef/tree/master/examples/QParity). Below, a more basic example is discussed.

## A simple example
Let _n_ ∊ ℕ*. We will consider the formula family containing QBF over variables _x₁_, ..., _xₙ_, _y₁_, ..., _yₙ_ of the form

Φ(_n_) = ∃ _x₁_ ∀ _y₁_ ... ∃ _xₙ_ ∀ _yₙ_ : φ(_x₁_, ..., _xₙ_, _y₁_, ..., _yₙ_)

where φ is the matrix is given by

φ(_x₁_, ..., _xₙ_, _y₁_, ..., _yₙ_) = (¬ _x₁_ ∨ ... ∨ ¬ _xₙ_) ∧ (_x₁_ ∨ _y₁_) ∧ ...  ∧ (_xₙ_ ∨ _yₙ_)

For instance, for _n_ = 2, the QBF is:

Φ(2) = ∃ _x₁_ ∀ _y₁_ ∃ _x₂_ ∀ _y₂_ : (¬ _x₁_ ∨ ¬ _x₂_) ∧ (_x₁_ ∨ _y₁_) ∧ (_x₂_ ∨ _y₂_)

In QBDef's formal language, Φ(_n_) is written as follows:

```
name: The simple parameterised example;
format: CNF;   /* possible formats are: CNF, circuit-prenex, circuit-nonprenex */

parameters: {
    n : int, `n >= 1`;
}

variables: {
    x(i)    where i in 1..n;
    y(i)    where i in 1..n;
}

blocks: {

    /* === Quantifier prefix === */
    
    define blocks grouped in QX {
        QX(i) := x(i);
    } where i in 1..n;

    define blocks grouped in QY {
        QY(i) := y(i);
    } where i in 1..n;

    define blocks grouped in QXY {
        QXY(i) := QX(i), QY(i);
    } where i in 1..n;

    define block Q := all blocks in QXY;

    all blocks in QX quantified with ∃;     /* it's also possible to write E */
    all blocks in QY quantified with ∀;     /* it's also possible to write A */

    /* === Matrix === */

    define blocks {
        NotX := ¬x(i);
    } where i in 1..n;

    define blocks grouped in XY {
        XY(i) := x(i), y(i);
    } where i in 1..n;

    define block φ := NotX, all blocks in XY;

    block NotX operated with ∨;
    all blocks in XY operated with ∨;      /* it's also possible to write OR  */
    block φ operated with ∧;               /* it's also possible to write AND */

    /* Define the output block: */
    define block Φ := Q, φ;

}

output block: Φ;
```

Suppose the previous piece of code is in some file `definition.txt` and we create a second file, `values.txt`, containing:

```
value: n = 2;
```

Now, if we execute `python3 QBDef.py definition.txt values.txt -QCIR` in a terminal, we get the following QCIR output:

```
#QCIR-G14
exists(1)
forall(3)
exists(2)
forall(4)
output(15)
12 = or(-1, -2)
13 = or(1, 3)
14 = or(2, 4)
15 = and(12, 13, 14)
```

If we execute `python3 QBDef.py definition.txt values.txt -QDIMACS`, we get the output in QDIMACS:

```
c Formula Family: The simple parameterised example
c Values: {'n': 2}
p cnf 4 3
e 1 0
a 3 0
e 2 0
a 4 0
-1 -2 0
1 3 0
2 4 0

```

# More documentation
This work belongs to my Bachelor's thesis, _A Formal Language and Tool for QBF Family Definitions_, written in 2020 at the KU Leuven. [The thesis text](https://github.com/alephnoell/QBDef/blob/master/documents/Thesis%20Text%20-%20A%20Formal%20Language%20and%20Tool%20for%20QBF%20Family%20Definitions.pdf) and the slides used for its defence can be found in the [`/documents`](https://github.com/alephnoell/QBDef/tree/master/documents) folder. These contain an in-depth discussion of the tool and its implementation, as well as many other examples.

Besides, this work was presented at the QBF Workshop 2020. The extended abstract is also available in the [`/documents`](https://github.com/alephnoell/QBDef/tree/master/documents) folder, alongside the video recording of the talk and the slides used for it.

Any of these documents, alongside the cheat sheet, can serve as documentation on how to use QBDef.

# Bugs and further development
If you find bugs or errors when trying to use QBDef, please let me know at noel.arteche@gmail.com. Besides, feel free to use this code and modify it for your own purposes.

# Contents of the repository

* [`QBDef.py`](https://github.com/alephnoell/QBDef/blob/master/QBDef.py): Python script to run the tool.
* [`qcir-to-qdimacs.py `](https://github.com/alephnoell/QBDef/blob/master/qcir-to-qdimacs.py): third-party Python script for QCIR-to-QDIMACS conversion.
* [`QBDef Cheatsheet.pdf`](https://github.com/alephnoell/QBDef/blob/master/QBDef%20Cheatsheet.pdf): brief cheat sheet on how to use the language and the tool.
* [`/examples`](https://github.com/alephnoell/QBDef/tree/master/examples): example definitions in the formal language.
* [`/documents`](https://github.com/alephnoell/QBDef/tree/master/documents): some documents related to this project. These are an extended abstract presented at the QBF Workshop 2020, my Bachelor's thesis, to which this work belongs, as well as slides from talks given about this project.
* `/src`: source code and development files.
