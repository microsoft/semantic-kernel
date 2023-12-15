# Split text from scraper into questions and answers

def split(input_text):
    output_dict = {}
    output_dict["title"] = input_text["title"]
    
    # get all the lines in the document
    i = 0 
    question_lines = []
    all_lines = []
    for line in input_text["content"].split("\n"):
        all_lines.append(line)
        if "?" in line:
            question_lines.append(i)
        i = i + 1 


    # create lists of all the questions and paragraphs in order
    if question_lines[0] != 0:
        paragraphs = ["\n".join(all_lines[0:question_lines[0]-1])]
    else:
        paragraphs = []
    questions = []

    for i in range(0, len(question_lines)-1):
        paragraph = "\n".join(all_lines[question_lines[i]+1:question_lines[i+1]])
        if len(paragraph) > 0:
            paragraphs.append(paragraph)
            questions.append(all_lines[question_lines[i]])

    paragraph = "\n".join(all_lines[question_lines[len(question_lines)-1]+1:]) # last paragraph
    if len(paragraph) > 0:
        paragraphs.append(paragraph)
        questions.append(all_lines[question_lines[len(question_lines)-1]])


    # if the first line is not a question, then 
    # the first paragraph is just a paragraph not an answer
    if len(paragraphs) > len(questions):
        output_dict["first_paragraph"] = paragraphs[0]
        del paragraphs[0]
    else:
        output_dict["first_paragraph"] = None


    output_dict["answers"] = paragraphs
    output_dict["questions"] = questions

    return output_dict
