# Create the folder containing your GraphRag index
mkdir ./ragtest

# Download a book to use as your input
curl https://www.gutenberg.org/cache/epub/24022/pg24022.txt -o ./ragtest/input/book.txt

# Initialize the GraphRag setup
graphrag init --root ./ragtest
