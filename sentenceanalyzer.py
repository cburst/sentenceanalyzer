import sys
import os
import mimetypes
import nltk.data
import subprocess
import csv
import glob
import re


def check_pdflatex():
    try:
        # Attempt to run pdflatex to see if it's installed
        subprocess.run(["pdflatex", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        # pdflatex not found, exit the script with a helpful message
        print("pdflatex is not installed. Please install a LaTeX distribution to continue.")
        print("For Linux, you can typically install TeX Live using your package manager, e.g., 'sudo apt-get install texlive'.")
        print("For Windows, you can download and install MiKTeX or TeX Live from their respective websites.")
        print("For MacOS, MacTeX is a popular choice, available at https://www.tug.org/mactex/.")
        sys.exit(1)

# Usage
check_pdflatex()

def check_jre():
    try:
        # Attempt to run java to see if JRE is installed
        subprocess.run(["java", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        # JRE not found, exit the script with a helpful message
        print("Java Runtime Environment (JRE) is not installed. Please install JRE to continue.")
        print("You can download it from https://www.oracle.com/java/technologies/javase-jre8-downloads.html")
        print("Or, use OpenJDK which is available at https://adoptopenjdk.net/")
        sys.exit(1)

# Usage
check_jre()

def main():

    if len(sys.argv) != 2:
        print("Usage: {} <textfile>".format(sys.argv[0]))
        sys.exit(1)

    filename = sys.argv[1]

    if not os.path.isfile(filename):
        print("Error: File does not exist or is a directory.")
        sys.exit(1)

    if not filename.endswith('.txt'):
        print("Error: File is not a .txt file.")
        sys.exit(1)

    file_type = mimetypes.guess_type(filename)[0]
    if file_type is None or not file_type.startswith('text/'):
        print("Error: File is not a text file.")
        sys.exit(1)

    print("Processing text file:", filename)

    # filename processing
    append_text = "_process"
    length = len(filename) - 4
    filenameproc = filename[:length] + append_text + ".txt"

    # Process and save the file
    process_and_save_file(filename, filenameproc)

    output_dir = "{}_sentences".format(os.path.splitext(filename)[0])
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

def process_and_save_file(filename, filenameproc):
    """
    Processes the input file by replacing line breaks with spaces, keeping only Latin characters,
    basic punctuation, numerals, whitespaces, ampersands, and percent symbols,
    and saving the content to a new file.
    """
    with open(filename, 'r', encoding='utf-8') as file:
        text = file.read()

    # Replace line breaks with spaces
    text = text.replace('\n', ' ')

    # Keep only Latin characters, basic punctuation, numerals, whitespaces, ampersands, and percent symbols
    text = re.sub(r'[^a-zA-Z0-9 ,.?!;:\'\"()\[\]{}&%-]', '', text)

    with open(filenameproc, 'w', encoding='utf-8') as file:
        file.write(text)


def tokenize_sentences(input_file, output_dir):
    """
    Tokenize the text in input_file into sentences and save each sentence
    as a separate file in output_dir.
    """
    # Initialize NLTK sentence tokenizer
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    with open(input_file, 'r') as f:
        text = f.read()

    sentences = tokenizer.tokenize(text)
    os.makedirs(output_dir, exist_ok=True)

    for i, sentence in enumerate(sentences, start=1):
        sentence_filename = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(input_file))[0]}-{i:03d}.txt")
        with open(sentence_filename, 'w') as sentence_file:
            sentence_file.write(sentence)

    print(f"Sentences have been separated and saved in the '{output_dir}' directory.")


def analyze_text(output_dir, filenameproc):
    """
    Analyze all files in output_dir using analyzeFolder.py.
    Rename each file based on the analysis result in the generated CSV file.
    """
    # Run analyzeFolder.py on the output_dir
    analysis_csv = os.path.join(output_dir, "folder_analysis.csv")
    subprocess.run(["python3", "analyzeFolder.py", output_dir, analysis_csv])

    # Read the generated CSV and process each file
    with open(analysis_csv, newline='') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  # Skip the header row

        for row in reader:
            filename = row[0]  # The first cell is the filename
            sentence_file = os.path.join(output_dir, filename)

            # Checking the 6th cell after the filename (7th cell in the row)
            if row[7].isdigit() and int(row[7]) > 0:
                new_sentence_filename = f"{os.path.splitext(sentence_file)[0]}-C{os.path.splitext(sentence_file)[1]}"
            else:
                new_sentence_filename = f"{os.path.splitext(sentence_file)[0]}-S{os.path.splitext(sentence_file)[1]}"

            if new_sentence_filename != sentence_file:
                os.rename(sentence_file, new_sentence_filename)

    analysis_csv = os.path.join(output_dir, "analysis.csv")
    subprocess.run(["python3", "analyzeText.py", filenameproc, analysis_csv])

def transpose_csv(input_csv, output_csv):
    with open(input_csv, newline='') as infile, open(output_csv, 'w', newline='') as outfile:
        reader = csv.reader(infile)
        headers = next(reader)[1:]
        data = list(reader)

        writer = csv.writer(outfile)
        writer.writerow(['Measurement', 'Data'])

        for i, header in enumerate(headers):
            row = [header] + [data[j][i+1] for j in range(len(data))]
            writer.writerow(row)

def create_latex_document(files_to_combine, latex_file, output_csv):
    with open(latex_file, 'w') as f:
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
            with open(file, 'r') as content_file:
                content = content_file.read().strip()

                # Escape special LaTeX characters
                content = content.replace('&', '\\&').replace('%', '\\%').replace('$', '\\$').replace('#', '\\#').replace('_', '\\_').replace('{', '\\{').replace('}', '\\}').replace('^', '\\^{}').replace('~', '\\~{}')

                if "-C.txt" in file:
                    # Add highlighted content for complex sentences
                    f.write(f"\\textcolor{{orange}}{{{content}}} ")
                else:
                    # Add regular content
                    f.write(f"{content} ")

        # Add CSV data
        f.write(r"""\newpage 
\textbf{L2SCA Analysis}\newline \newline 
\csvautobooktabular{""" + output_csv + r"""}
\end{document}""")



def generate_pdf(latex_file, filename):
    """
    Generate a PDF from a LaTeX file using pdflatex.
    The PDF is saved in the original directory with the original filename
    and '_analysis' appended.
    """
    output_dir = os.path.dirname(latex_file)
    base_name = os.path.splitext(filename)[0]
    pdf_output_filename = f"{base_name}_analysis.pdf"

    if subprocess.run(["command", "-v", "pdflatex"], capture_output=True).returncode == 0:
        subprocess.run(["pdflatex", "-output-directory=" + output_dir, latex_file], stdout=subprocess.DEVNULL)
        os.rename(os.path.join(output_dir, "combined_sentences.pdf"), pdf_output_filename)
        print("PDF generated:", pdf_output_filename)
    else:
        print("pdflatex not found. Please install TeX Live or MacTeX to generate the PDF.")

def cleanup_files(filenameproc, output_dir):
    try:
        os.remove(filenameproc)
        for f in glob.glob(os.path.join(output_dir, "*")):
            os.remove(f)
        os.rmdir(output_dir)
    except Exception as e:
        print("Error during cleanup:", e)

if __name__ == "__main__":
    main()
