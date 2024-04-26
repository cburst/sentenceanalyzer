import sys
import os
import mimetypes
import nltk.data
import subprocess
import csv
import glob
import re
import shutil


def check_pdflatex():
    # Use shutil.which to check for the presence of the pdflatex executable in the system PATH
    if shutil.which("pdflatex") is None:
        # pdflatex not found, exit the script with a helpful message
        print("pdflatex is not installed. Please install a LaTeX distribution to continue.")
        print("For Linux, you can typically install TeX Live using your package manager, e.g., 'sudo apt-get install texlive'.")
        print("For Windows, you can download and install MiKTeX or TeX Live from their respective websites.")
        print("For MacOS, MacTeX is a popular choice, available at https://www.tug.org/mactex/.")
        sys.exit(1)
    print("pdflatex is installed and available.")

# Usage
check_pdflatex()

def check_jre():
    # Use shutil.which to check for the presence of the java executable in the system PATH
    if shutil.which("java") is None:
        # JRE not found, exit the script with a helpful message
        print("Java Runtime Environment (JRE) is not installed. Please install JRE to continue.")
        print("You can download it from https://www.oracle.com/java/technologies/javase-jre8-downloads.html")
        print("Or, use OpenJDK which is available at https://adoptopenjdk.net/")
        sys.exit(1)
    print("Java Runtime Environment (JRE) is installed and available.")
    
# Usage
check_jre()

def check_nltk_availability():
    try:
        import nltk
        # Try loading a specific tokenizer to check if NLTK data is available
        nltk.data.find('tokenizers/punkt')
    except ImportError:
        print("NLTK library is not installed. Please install it using 'pip install nltk'.")
        sys.exit(1)
    except LookupError:
        print("NLTK data is missing. You can download it using the following Python commands:")
        print("import nltk")
        print("nltk.download('punkt')")
        sys.exit(1)


def is_text_file(filename):
    # Check based on MIME type first
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type not in ['text/plain']:
        return False

    # Try to open and read a part of the file to confirm
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            f.read(1024)  # Read first 1KB of the file to check if readable as text
        return True
    except UnicodeDecodeError:
        return False

def main():

    # First, check for NLTK availability
    check_nltk_availability()

    if len(sys.argv) != 2:
        print("Usage: {} <textfile>".format(sys.argv[0]))
        sys.exit(1)

    filename = sys.argv[1]

    if not os.path.isfile(filename) or not is_text_file(filename):
    	print("Error: The specified file does not exist, is a directory, or is not a plain .txt file.")
    	sys.exit(1)

    print("Processing text file:", filename)
    append_text = "_process"
    base_name = os.path.splitext(filename)[0]  # Securely strip extension
    filenameproc = f"{base_name}{append_text}.txt"

    # Process and save the file
    process_and_save_file(filename, filenameproc)

    output_dir = os.path.join(os.path.dirname(filename), f"{os.path.splitext(os.path.basename(filename))[0]}_sentences")
    tokenize_sentences(filenameproc, output_dir)

    sentence_files = sorted(glob.glob(os.path.join(output_dir, "*.txt")))
    analyze_text(output_dir, filenameproc)

    analysis_csv = os.path.join(output_dir, "analysis.csv")
    transposed_csv = os.path.join(output_dir, "analysis_transposed.csv")
    transpose_csv(analysis_csv, transposed_csv)

    files_to_combine = sorted(glob.glob(os.path.join(output_dir, "*[0-9][0-9][0-9]-[CS].txt")))
    latex_file = os.path.join(output_dir, "combined_sentences.tex")
    create_latex_document(files_to_combine, latex_file, transposed_csv)
    generate_pdf(latex_file, filename)
	
    cleanup_files(filenameproc, output_dir)

    print("File analyzed.")

# Assuming the pattern is defined globally
pattern = re.compile(r'[^a-zA-Z0-9 ,.?!;:\'\"()\[\]{}&%-]')

def process_and_save_file(filename, filenameproc):
    """
    Processes the input file by replacing line breaks with spaces, keeping only Latin characters,
    basic punctuation, numerals, whitespaces, ampersands, and percent symbols,
    and saving the content to a new file.
    """
    try:
        # Use 'newline' to handle different newlines across platforms
        with open(filename, 'r', encoding='utf-8', newline='') as file:
            with open(filenameproc, 'w', encoding='utf-8') as outfile:
                for line in file:
                    processed_line = line.replace('\n', ' ')  # Handles newline within the universal newline mode
                    processed_line = pattern.sub('', processed_line)
                    outfile.write(processed_line)
    except OSError as e:
        print(f"An error occurred while processing the file: {e}")


def tokenize_sentences(input_file, output_dir):
    """
    Tokenize the text in input_file into sentences and save each sentence as a separate file in output_dir.
    """
    # Initialize NLTK sentence tokenizer
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()

        sentences = tokenizer.tokenize(text)
        for i, sentence in enumerate(sentences, start=1):
            sentence_filename = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(input_file))[0]}-{i:03d}.txt")
            with open(sentence_filename, 'w', encoding='utf-8') as sentence_file:
                sentence_file.write(sentence)

        print(f"Sentences have been separated and saved in the '{output_dir}' directory.")
    except IOError as e:
        print(f"An error occurred while accessing files: {e}")
    except OSError as e:
        print(f"An operating system error occurred: {e}")


def analyze_text(output_dir, filenameproc):
    """
    Analyze all files in output_dir using analyzeFolder.py.
    Rename each file based on the analysis result in the generated CSV file.
    """
    # Define paths to the scripts and CSV files
    analysis_folder_csv = os.path.join(output_dir, "folder_analysis.csv")
    analysis_text_csv = os.path.join(output_dir, "analysis.csv")
    
    # Define the Python executable
    python_exec = sys.executable

    # Run analyzeFolder.py on the output_dir
    folder_result = subprocess.run([python_exec, "analyzeFolder.py", output_dir, analysis_folder_csv], capture_output=True, text=True)
    print("analyzeFolder.py output:", folder_result.stdout)
    if folder_result.returncode != 0:
        print("Error running analyzeFolder.py:", folder_result.stderr)
        return
    else:
        print("analyzeFolder.py completed successfully.")

    # Process CSV output from analyzeFolder.py
    try:
        with open(analysis_folder_csv, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # Skip the header row

            for row in reader:
                if len(row) < 8:
                    continue  # Skip rows that do not have enough columns

                filename = row[0]  # The first cell is the filename
                sentence_file = os.path.join(output_dir, filename)
                analysis_result = row[7]

                # Determine new filename based on analysis result
                new_suffix = "-C" if analysis_result.isdigit() and int(analysis_result) > 0 else "-S"
                new_sentence_filename = f"{os.path.splitext(sentence_file)[0]}{new_suffix}{os.path.splitext(sentence_file)[1]}"

                if new_sentence_filename != sentence_file:
                    os.rename(sentence_file, new_sentence_filename)

    except Exception as e:
        print(f"Failed to process CSV: {e}")

    # Run analyzeText.py on the processed data
    text_result = subprocess.run([python_exec, "analyzeText.py", filenameproc, analysis_text_csv], capture_output=True, text=True)
    print("analyzeText.py output:", text_result.stdout)
    if text_result.returncode != 0:
        print("Error running analyzeText.py:", text_result.stderr)
    else:
        print("analyzeText.py completed successfully.")

def transpose_csv(input_csv, output_csv):
    try:
        with open(input_csv, 'r', encoding='utf-8', newline='') as infile, \
             open(output_csv, 'w', encoding='utf-8', newline='') as outfile:

            reader = csv.reader(infile)
            try:
                headers = next(reader)[1:]  # Skip the first column header
            except StopIteration:
                print("Input CSV is empty.")
                return

            data = list(reader)
            if not data:
                print("No data rows in input CSV.")
                return

            writer = csv.writer(outfile)
            writer.writerow(['Measurement', 'Data'])

            for i, header in enumerate(headers):
                # Check if there are enough columns in the rows
                if all(len(row) > i+1 for row in data):
                    row = [header] + [data[j][i+1] for j in range(len(data))]
                    writer.writerow(row)
                else:
                    print(f"Not enough columns in data to match header index {i + 1}.")

    except IOError as e:
        print(f"An error occurred accessing the file: {e}")

def latex_escape(text):
    """
    Escapes special characters for LaTeX document.
    """
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '^': r'\^{}',
        '~': r'\~{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}'
    }
    regex = re.compile('|'.join(re.escape(key) for key in replacements.keys()))
    return regex.sub(lambda match: replacements[match.group()], text)

def create_latex_document(files_to_combine, latex_file, output_csv):
    """
    Creates a LaTeX document from text files and a CSV file.
    """
    try:
        with open(latex_file, 'w', encoding='utf-8') as f:
            # LaTeX document header
            f.write(r"""\documentclass{article}
\usepackage{xcolor}
\usepackage{csvsimple}
\usepackage{booktabs}
\begin{document}
\indent \textbf{Analysis notes:} \newline
\indent This PDF file contains your text color-coded according to L2SCA analysis of syntactic complexity.
\begin{color}{orange}
Syntactically complex sentences have been highlighted in \textbf{orange}, so that you may write more sentences like these in the future. 
\end{color}
Try to combine sentences that are not highlighted to make them more syntactically complex. \newline
\newline
\indent \textbf{Use the following words to combine your sentences:} \newline 
\begin{color}{teal} 
\indent after, although, as, because, before, even if, how, if, since, so that, such that
\newline
\indent though, unless, until, when, whenever, where, whereas, wherever, and while. 
\end{color} \newline
\newline
\indent \textbf{Contact info:} \newline
\indent \begin{color}{teal} richard.rose@yonsei.ac.kr \end{color} \newline
\newline
\newline
\indent \textbf{Your text:} \newline
\indent """)

            # Add each file's content
            for file in files_to_combine:
                with open(file, 'r', encoding='utf-8') as content_file:
                    content = content_file.read().strip()
                    content = latex_escape(content)

                    if "-C.txt" in file:
                        # Add highlighted content for complex sentences
                        f.write(f"\\textcolor{{orange}}{{{content}}} ")
                    else:
                        # Add regular content
                        f.write(f"{content} ")

            # Add CSV data
            latex_path = output_csv.replace('\\', '/')  # Ensuring path compatibility in LaTeX
            f.write(r"""\newpage 
\textbf{L2SCA Analysis}\newline \newline 
\csvautobooktabular{""" + latex_path + r"""}
\end{document}""")

    except Exception as e:
        print(f"An error occurred while creating the LaTeX document: {e}")

def compile_latex(latex_file):
    """
    Compiles a LaTeX file into a PDF document.
    """
    try:
        subprocess.run(['pdflatex', latex_file], check=True)
        print(f"LaTeX document {latex_file} compiled successfully.")
    except subprocess.CalledProcessError:
        print("Failed to compile the LaTeX document.")

def generate_pdf(latex_file, filename):
    """
    Generate a PDF from a LaTeX file using pdflatex.
    The PDF is saved in the original directory with the original filename
    and '_analysis' appended.
    """
    output_dir = os.path.dirname(latex_file)
    base_name = os.path.splitext(filename)[0]
    pdf_output_filename = os.path.join(output_dir, f"{base_name}_analysis.pdf")

    if shutil.which("pdflatex"):
        result = subprocess.run(["pdflatex", "-output-directory=" + output_dir, latex_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            # Rename the output PDF to the desired name
            pdf_generated = os.path.join(output_dir, os.path.splitext(os.path.basename(latex_file))[0] + ".pdf")
            if os.path.exists(pdf_generated):
                os.rename(pdf_generated, pdf_output_filename)
                print("PDF generated:", pdf_output_filename)
            else:
                print("Expected PDF not found. Check LaTeX output for errors.")
        else:
            print("Error generating PDF:", result.stderr)
    else:
        print("pdflatex not found. Please install TeX Live or MacTeX to generate the PDF.")

def cleanup_files(filenameproc, output_dir):
    try:
        # Remove the processed file if it exists
        if os.path.exists(filenameproc):
            os.remove(filenameproc)
        
        # Use shutil.rmtree to handle directory cleanup, including non-empty directories
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

    except OSError as e:
        # Only print errors if they occur during cleanup
        print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    main()
