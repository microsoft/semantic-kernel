mkdir ./ragtest

curl https://www.gutenberg.org/cache/epub/24022/pg24022.txt -o ./ragtest/input/book.txt

# after fixing the setup

graphrag index --root ./ragtest