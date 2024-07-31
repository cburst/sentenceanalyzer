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
                if len(np_leaves) > 1:
                    complex_nominals.append(" ".join(np_leaves))
    return complex_nominals

# Argument parser setup
def parse_arguments():
    parser = argparse.ArgumentParser(description="Extract complex nominals from a text file using the Stanford Parser.")
    parser.add_argument("input_file", help="Path to the input text file")
    return parser.parse_args()

# Main function
def main():
    args = parse_arguments()

    # Read the text from the input file
    with open(args.input_file, 'r') as file:
        text = file.read()

    # Parse the text
    sentences = nltk.sent_tokenize(text)
    parse_trees = parser.raw_parse_sents(sentences)

    # Extract complex nominals
    complex_nominals = []
    for tree in parse_trees:
        complex_nominals.extend(extract_complex_nominals(tree))

    # Prepare the output filename
    output_filename = f"{os.path.splitext(args.input_file)[0]}_CNs.tsv"

    # Write the complex nominals to a TSV file
    with open(output_filename, 'w', newline='') as tsvfile:
        writer = csv.writer(tsvfile, delimiter='\t')
        writer.writerow(['CNs'])  # Header
        writer.writerow([', '.join(complex_nominals)])  # Complex nominals

    print(f"Complex Nominals saved to {output_filename}")

if __name__ == "__main__":
    main()