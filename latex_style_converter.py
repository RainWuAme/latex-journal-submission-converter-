import argparse
import os
import re
import shutil
import sys
from pathlib import Path

# This code is written by Rain Wu 2024-10-07
# Updated with improved error handling 2025-07-20


def extract_figure_names(content):
    # Regular expression to find \includegraphics commands, ignoring commented lines
    pattern = r'^(?!%).*\\includegraphics(?:\[.*?\])?\{(.*?)\}'

    # Use re.MULTILINE flag to match the start of each line
    figures = re.findall(pattern, content, re.MULTILINE)

    return figures


def copy_figures(figures, figure_path, target_dir):
    copied_count = 0
    for i, figure in enumerate(figures):
        # Extract the figure name from the path
        figure_name = Path(figure).stem
        # Construct the source path using figure_path
        source_path = Path(figure_path) / figure_name
        # Construct the target path
        target_path = target_dir / f'Fig{i+1}'

        # List of file extensions to check
        extensions = ['.pdf', '.png', '.jpg', '.jpeg']

        for ext in extensions:
            source_file = source_path.with_suffix(ext)
            if source_file.exists():
                target_file = target_path.with_suffix(ext)
                try:
                    shutil.copy(source_file, target_file)
                    copied_count += 1
                    break
                except Exception as e:
                    print(f"Error copying {source_file}: {e}")
                    return False
        else:
            print(f"Warning: No matching file found for {figure_name}")
    
    print(f"Successfully copied {copied_count} out of {len(figures)} figures")
    return True


def validate_inputs(main_name, figure_path, latexpand_path):
    """Validate that all required inputs exist and are accessible."""
    errors = []
    
    # Check if main LaTeX file exists
    if not Path(main_name).exists():
        errors.append(f"Main LaTeX file '{main_name}' does not exist")
    
    # Check if aux file exists (needed for bibexport)
    aux_file = main_name.replace(".tex", ".aux")
    if not Path(aux_file).exists():
        errors.append(f"Auxiliary file '{aux_file}' does not exist. Please compile your LaTeX document first.")
    
    # Check if figure path exists
    if not figure_path.exists():
        errors.append(f"Figure path '{figure_path}' does not exist")
    
    # Check if latexpand executable exists
    if not latexpand_path.exists():
        errors.append(f"Latexpand executable '{latexpand_path}' does not exist")
    elif latexpand_path.is_dir():
        errors.append(f"Latexpand path '{latexpand_path}' is a directory, not an executable file")
    
    return errors


def run_command_with_check(command, description):
    """Run a system command and check if it succeeded."""
    print(f"Running: {description}")
    try:
        result = os.system(command)
        if result != 0:
            print(f"Error: {description} failed with exit code {result}")
            return False
        return True
    except Exception as e:
        print(f"Error running {description}: {e}")
        return False


if __name__ == '__main__':
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Convert LaTeX files and extract figures.')
    parser.add_argument('--main_name', type=str,
                        default='Main.tex', help='Name of the main LaTeX file')
    parser.add_argument('--figure_path', type=str, default='../Figures',
                        help='Path to the figures directory relative to the main LaTeX file')
    parser.add_argument('--latexpand_path', type=str,
                        default='../latexpand', help='Path to the latexpand executable')

    # Parse the arguments
    args = parser.parse_args()
    main_name = args.main_name
    figure_path = Path(args.figure_path)
    latexpand_path = Path(args.latexpand_path)

    print("LaTeX Style Converter Starting...")
    print(f"Main file: {main_name}")
    print(f"Figure path: {figure_path}")
    print(f"Latexpand path: {latexpand_path}")
    print()

    # Validate inputs before proceeding
    validation_errors = validate_inputs(main_name, figure_path, latexpand_path)
    if validation_errors:
        print("Validation errors found:")
        for error in validation_errors:
            print(f"  - {error}")
        print("\nPlease fix these issues and try again.")
        sys.exit(1)

    print("All inputs validated successfully!")
    print("\nStart converting...")
    
    # Track success of each step
    success = True
    
    try:
        # Create target directory
        target_dir = Path('transformed')
        if not target_dir.exists():
            target_dir.mkdir(parents=True)
            print(f"Created target directory: {target_dir}")

        # Create bib file
        aux_file = main_name.replace(".tex", ".aux")
        bib_command = f'bibexport -o {target_dir / "References.bib"} {aux_file}'
        if not run_command_with_check(bib_command, "bibliography export"):
            print("Warning: Bibliography export failed. You may need to create References.bib manually.")
            # Don't fail completely, as this might be recoverable

        # Convert multiple Latex files into single long Latex file
        latexpand_command = f'perl {latexpand_path} {main_name} > tmp.tex'
        if not run_command_with_check(latexpand_command, "LaTeX expansion"):
            print("Error: Failed to merge LaTeX files")
            success = False
        else:
            # Check if tmp.tex was actually created and has content
            tmp_file = Path('tmp.tex')
            if not tmp_file.exists() or tmp_file.stat().st_size == 0:
                print("Error: Expanded LaTeX file (tmp.tex) was not created or is empty.")
                success = False

        if success:
            # Load the long Latex file
            latex_file = Path('tmp.tex')
            try:
                with latex_file.open('r', encoding="utf-8") as file:
                    content = file.read()
                print("Successfully read expanded LaTeX file")
            except Exception as e:
                print(f"Error reading expanded LaTeX file: {e}")
                success = False

        if success:
            # Extract figures to the target directory
            figures = extract_figure_names(content)
            print(f"Found {len(figures)} figures to copy")
            
            if figures:
                if not copy_figures(figures, figure_path, target_dir):
                    print("Error: Failed to copy all figures")
                    success = False
            else:
                print("No figures found in the document")

        if success:
            # Move the main tex file and copy style files to the target directory
            try:
                shutil.move('tmp.tex', target_dir / 'Main.tex')
                print("Moved main LaTeX file to target directory")
                
                # Copy style files
                file_types = [('*.cls', 'class'), ('*.sty', 'style'), ('*.bst', 'bibliography style')]
                for pattern, file_type in file_types:
                    files = list(Path('.').glob(pattern))
                    if files:
                        for file in files:
                            shutil.copy(file, target_dir)
                        print(f"Copied {len(files)} {file_type} file(s)")
                
            except Exception as e:
                print(f"Error moving/copying files: {e}")
                success = False

        if success:
            # cd to the target directory and read the main file
            try:
                os.chdir(target_dir)
                latex_file = Path('Main.tex')
                with latex_file.open('r', encoding="utf-8") as file:
                    content = file.read()
                print("Successfully read main file in target directory")
            except Exception as e:
                print(f"Error reading main file in target directory: {e}")
                success = False

        if success:
            try:
                # Rename the figures in the Main.tex file to 'Fig1', 'Fig2', etc.
                for i, figure in enumerate(figures):
                    figure_name = Path(figure).name
                    new_name = f'Fig{i+1}'
                    content = content.replace(figure_name, new_name)

                # Remove the figures path so that it just reads the figures in the same folder
                content = re.sub(
                    r'\\graphicspath\s*\{[^}]*\}', '', content, flags=re.DOTALL)

                # Remove the \bibliography{../LibraryAllReferences} and add \bibliography{References}
                content = re.sub(
                    r'\\bibliography\s*\{[^}]*\}', r'\\bibliography{References}', content, flags=re.DOTALL)

                # Write the updated content
                with latex_file.open('w', encoding="utf-8") as file:
                    file.write(content)
                print("Successfully updated figure references and bibliography path")
                
            except Exception as e:
                print(f"Error updating LaTeX content: {e}")
                success = False

    except Exception as e:
        print(f"Unexpected error during conversion: {e}")
        success = False

    # Final status report
    print("\n" + "="*50)
    if success:
        print('CONVERSION COMPLETE! All files are in the transformed folder.')
        print('Now, it is your responsibility to proofread :)')
    else:
        print('CONVERSION FAILED! Please check the errors above and try again.')
        print('Common solutions:')
        print('  - Ensure you have compiled your LaTeX document (to generate .aux file)')
        print('  - Check that the figure path is correct')
        print('  - Verify the latexpand executable path (should point to the file, not directory)')
        sys.exit(1)