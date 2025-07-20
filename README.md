# LaTeX Style Converter

When submitting journal articles, most journals require a single .tex file and figures named as Fig1, Fig2, etc.
This tool helps convert LaTeX documents by extracting figures, creating a single main file, and generating a .bib file with only cited references.

## Setup and Usage

1. **Preparation**
   - Copy `latex_style_converter.py` to your local folder.

2. **Running the Converter**
   - Execute the script:
     ```
     python latex_style_converter.py --main_name Main.tex --figure_path ../Figures --latexpand_path ../latexpand
     ```
     Please modify your main_name, figure_path, and latexpand_path if needed.

3. **Note**
   - For Windows user, wsl is recommended.


## Additional Features (already included in the `latex_style_converter.p` code)

### Creating a .bib File with Only Cited References

#### For Linux Users:
```
bibexport -o References.bib {main}.aux
```
Replace `{main}` with your main LaTeX file name.

#### For Windows Users:
- Option 1: Stop using Windows. Use Linux 😉
- Option 2: Use JabRef
   1. Install JabRef
   2. Run:
     ```
     jabref.jar -a filename[.aux],newBibFile[.bib]
     ```
   3. Or use jabref gui as mentioned in the References

### Creating a Single Main.tex File

To combine all subfiles into a single main file:

1. Run:
   ```
   perl latexpand {main}.tex > new_main.tex
   ```
   Replace `{main}` with your main LaTeX file name.

## Generating Tex Files and Renaming Figures

This is handled automatically by running:
```
python latex_style_converter.py
```

## References

1. [Creating .bib file containing only the cited references of a bigger .bib file](https://tex.stackexchange.com/questions/41821/creating-bib-file-containing-only-the-cited-references-of-a-bigger-bib-file)

