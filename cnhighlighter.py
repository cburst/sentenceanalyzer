import os
import nltk
from nltk.parse.stanford import StanfordParser
import argparse
import csv

# Set the path to the Stanford Parser directory
stanford_parser_dir = 'stanford-parser-full-2020-11-17'
os.environ['STANFORD_PARSER'] = os.path.join(stanford_parser_dir, 'stanford-parser.jar')
os.environ['STANFORD_MODELS'] = os.path.join(stanford_parser_dir, 'stanford-parser-4.2.0-models.jar')

# Set the path to the parser and models
parser_path = os.path.join(stanford_parser_dir, 'stanford-parser.jar')
models_path = os.path.join(stanford_parser_dir, 'stanford-parser-4.2.0-models.jar')

# Initialize the Stanford Parser
parser = StanfordParser(model_path="edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz")

# Function to extract complex nominals from parsed trees
def extract_complex_nominals(parse_trees):
    complex_nominals = []
    for tree in parse_trees:
        for subtree in tree.subtrees():
            if subtree.label() == 'NP':  # Noun Phrase
                np_leaves = subtree.leaves()
                if len(np_leaves) > 2:  # Only include complex nominals with more than two words
                    complex_nominals.append(" ".join(np_leaves))
    return complex_nominals

# Argument parser setup
def parse_arguments():
    parser = argparse.ArgumentParser(description="Extract complex nominals from a text file and generate a PDF with specific phrases underlined.")
    parser.add_argument("input_file", help="Path to the input text file")
    return parser.parse_args()

# Function to read the original text file
def read_text_file(text_file):
    with open(text_file, 'r') as file:
        return file.read()

# Function to read the complex nominals from the TSV file
def read_complex_nominals(tsv_file):
    with open(tsv_file, 'r') as file:
        reader = csv.reader(file, delimiter='\t')
        next(reader)  # Skip header
        row = next(reader)
        return [cn.strip() for cn in row[0].split(', ') if cn.strip()]

# Function to generate LaTeX code with the specified phrases underlined
def generate_latex(text, phrases_to_underline):
    latex_code = r"""\documentclass{article}
\usepackage{ulem}
\usepackage{xcolor}
\usepackage{geometry}
\geometry{a4paper, margin=1in}
\sloppy
\hyphenpenalty=10000
\tolerance=1000
\begin{document}
\indent \textbf{Analysis notes:} \newline
\indent This PDF file contains your text underlined using the Stanford Parser to emphasize the presence of complex nominals, which in turn are associated with syntactic complexity. Complex nominals are essentially sophisticated names that include several words or phrases as part of the name. Try to use complex nominals often, but as efficiently as possible.
\newline
\newline
\indent \textbf{Contact info:} \newline
\indent \begin{color}{teal} richard.rose@yonsei.ac.kr \end{color} \newline
\newline
\newline
\indent \textbf{Your text:} 
\indent


"""
    for phrase in phrases_to_underline:
        text = text.replace(phrase, r"\uline{" + phrase + r"}")
    latex_code += text + "\n\\end{document}"
    return latex_code

# Main function
def main():
    args = parse_arguments()

    # Read the text from the input file
    text = read_text_file(args.input_file)

    # Parse the text
    sentences = nltk.sent_tokenize(text)
    parse_trees = parser.raw_parse_sents(sentences)

    # Extract complex nominals
    complex_nominals = []
    for tree in parse_trees:
        complex_nominals.extend(extract_complex_nominals(tree))

    # Replace -LRB- and -RRB- with commas
    complex_nominals = [cn.replace('-LRB-', ',').replace('-RRB-', ',') for cn in complex_nominals]

    # Prepare the output filename for TSV
    output_tsv_filename = f"{os.path.splitext(args.input_file)[0]}_CNs.tsv"

    # Write the complex nominals to a TSV file
    with open(output_tsv_filename, 'w', newline='') as tsvfile:
        writer = csv.writer(tsvfile, delimiter='\t')
        writer.writerow(['CNs'])  # Header
        writer.writerow([', '.join(complex_nominals)])  # Complex nominals

    print(f"Complex Nominals saved to {output_tsv_filename}")

    # Read the complex nominals from the TSV file
    complex_nominals = read_complex_nominals(output_tsv_filename)

    # Count the total number of complex nominals
    total_complex_nominals = len(complex_nominals)
    print(f"Total number of complex nominals: {total_complex_nominals}")

    # Generate LaTeX code with the phrases underlined
    latex_code = generate_latex(text, complex_nominals)

    # Write LaTeX code to a .tex file
    tex_file = f"{os.path.splitext(args.input_file)[0]}.tex"
    with open(tex_file, 'w') as file:
        file.write(latex_code)

    # Compile LaTeX code to PDF
    os.system(f"pdflatex {tex_file}")

    print(f"PDF generated: {os.path.splitext(tex_file)[0]}.pdf")

if __name__ == "__main__":
    main()